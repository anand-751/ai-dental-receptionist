# from fastapi import APIRouter, WebSocket, WebSocketDisconnect
# import json
# import uuid
# import asyncio

# from backend.core.intent_classifier import classify_intent
# from backend.core.response_router import route_intent
# from backend.tools.calendar.token_store import get_refresh_token

# from backend.core.call_manager import (
#     can_accept_call,
#     add_active_call,
#     remove_active_call,
#     add_to_queue,
#     pop_next_from_queue,   
#     active_calls,
#     waiting_queue,
# )

# from backend.core.profile_store import LATEST_PROFILE

# router = APIRouter(
#     prefix="/conversation",
#     tags=["conversation"]
# )


# @router.websocket("/stream")
# async def conversation_stream(websocket: WebSocket):
#     await websocket.accept()
#     client_id = str(uuid.uuid4())

#     # QUEUE LOGIC
#     if not can_accept_call():
#         add_to_queue(client_id)
#         try:
#             await websocket.send_json({"type": "busy"})
#         except:
#             return

#         # Wait until promoted
#         while client_id in waiting_queue:
#             await asyncio.sleep(1)

#     add_active_call(client_id)
#     print(f"🟢 Active calls: {len(active_calls)}")

#     # SEND START SIGNAL
#     try:
#         await websocket.send_json({"type": "start"})
#     except:
#         return

#     refresh_token = get_refresh_token()

#     profile = LATEST_PROFILE if LATEST_PROFILE else {
#         "name": "Guest",
#         "phone": None,
#         "email": None,
#     }

#     session = {
#         "booking_state": None,
#         "booking_data": {},
#         "reschedule_state": None,
#         "reschedule_data": {},
#         "clinic_refresh_token": refresh_token,
#         "user_profile": profile,
#         "patient_name": profile.get("name"),
#         "patient_phone": profile.get("phone"),
#     }

#     print("🔐 SESSION STARTED WITH PROFILE:", profile)

#     try:
#         while True:
#             raw = await websocket.receive_text()
#             print(f"⬅️ RAW RECV: {raw}")

#             try:
#                 payload = json.loads(raw)
#             except Exception as e:
#                 print(f"JSON Parse Error: {e}")
#                 continue

#             incoming_profile = payload.get("user_profile")

#             if incoming_profile and incoming_profile.get("name"):
#                 session["user_profile"] = incoming_profile
#                 session["patient_name"] = incoming_profile.get("name")
#                 session["patient_phone"] = incoming_profile.get("phone")

#                 print("✅ PROFILE UPDATED FROM PAYLOAD:", session["user_profile"])

#             user_input = payload.get("user_input", "").strip()
#             if not user_input:
#                 continue

#             force_process = (
#                 session.get("booking_state") == "awaiting_slot" or
#                 session.get("reschedule_state") is not None
#             )

#             if force_process or user_input.endswith((".", "?", "!")) or len(user_input) > 15:
#                 try:
#                     intent = classify_intent(user_input)

#                     print(f"🤖 Processing '{intent}' for user:", session["patient_name"])
                    
#                     if session.get("booking_state") == "slot_selected" and session.get("payment_status") != "completed":

#                         # First time → create Stripe session
#                         if not session.get("payment_status"):
#                             session["payment_status"] = "pending"

#                             await websocket.send_json({
#                                 "response": "Great! Your slot is selected. Please complete payment using the link below.",
#                                 "type": "payment_required"
#                             })
#                             continue

#                         # Waiting for confirmation
#                         if session.get("payment_status") == "pending":
#                             if user_input.lower() == "paid":
#                                 session["payment_status"] = "completed"

#                                 await websocket.send_json({
#                                     "response": "Payment verified ✅ Confirming your appointment..."
#                                 })

#                                 session["booking_state"] = "confirm_booking"
#                             else:
#                                 await websocket.send_json({
#                                     "response": "Please complete the payment to proceed."
#                                 })
#                                 continue

#                     response = await route_intent(
#                         intent=intent,
#                         text=user_input,
#                         session=session
#                     )

#                     # response is never None
#                     if response is None:
#                         response = "Sorry, I couldn't process that. Please try again."

#                     await websocket.send_json({"response": response})

#                 except Exception as route_err:
#                     print(f"❌ ROUTING ERROR: {route_err}")
#                     await websocket.send_json({
#                         "response": "I encountered an error processing that."
#                     })

#     except WebSocketDisconnect:
#         print(f"🔌 Client {client_id} disconnected")
#         remove_active_call(client_id)

#         #  Promote next queued client
#         next_client = pop_next_from_queue()
#         if next_client:
#             print(f"🚀 Promoted from queue: {next_client}")

#     except Exception as e:
#         print(f"💀 CRITICAL WS ERROR: {e}")
#         remove_active_call(client_id)

#         #  Promote next queued client
#         next_client = pop_next_from_queue()
#         if next_client:
#             print(f"🚀 Promoted from queue: {next_client}")

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import uuid
import asyncio
import os

from backend.core.intent_classifier import classify_intent
from backend.core.response_router import route_intent
from backend.tools.calendar.token_store import get_refresh_token

from backend.core.call_manager import (
    can_accept_call,
    add_active_call,
    remove_active_call,
    add_to_queue,
    pop_next_from_queue,
    active_calls,
    waiting_queue,
)

from backend.core.profile_store import LATEST_PROFILE

router = APIRouter(prefix="/conversation", tags=["conversation"])


# ======================= STRIPE HELPERS =======================

async def create_stripe_checkout(frontend_url: str) -> dict:
    try:
        import stripe
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
        if not stripe.api_key:
            print("❌ STRIPE_SECRET_KEY not set")
            return {"ok": False, "error": "STRIPE_SECRET_KEY not configured"}

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            line_items=[{
                "price_data": {
                    "currency": "inr",
                    "product_data": {"name": "Dental Appointment Booking Fee"},
                    "unit_amount": 50000,  # ₹500
                },
                "quantity": 1,
            }],
            success_url=f"{frontend_url}/payment-success",
            cancel_url=f"{frontend_url}/payment-cancel",
        )

        print(f"✅ Stripe session: {checkout_session.id}")
        return {"ok": True, "url": checkout_session.url, "session_id": checkout_session.id}

    except Exception as e:
        print(f"❌ Stripe error: {e}")
        return {"ok": False, "error": str(e)}


async def verify_stripe_payment(session_id: str) -> bool:
    try:
        import stripe
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
        if not stripe.api_key or not session_id:
            print("⚠️ Stripe verify skipped — dev mode")
            return True
        s = stripe.checkout.Session.retrieve(session_id)
        paid = s.payment_status == "paid"
        print(f"{'✅' if paid else '⚠️'} Stripe status={s.payment_status}")
        return paid
    except Exception as e:
        print(f"❌ Stripe verify error: {e}")
        return True  # fallback accept


# ======================= WEBSOCKET HANDLER =======================

@router.websocket("/stream")
async def conversation_stream(websocket: WebSocket):
    await websocket.accept()
    client_id = str(uuid.uuid4())

    # ── Queue ──
    if not can_accept_call():
        add_to_queue(client_id)
        try:
            await websocket.send_json({"type": "busy"})
        except Exception:
            return
        while client_id in waiting_queue:
            await asyncio.sleep(1)

    add_active_call(client_id)
    print(f"🟢 Active calls: {len(active_calls)}")

    try:
        await websocket.send_json({"type": "start"})
    except Exception:
        return

    refresh_token = get_refresh_token()
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3001")

    profile = LATEST_PROFILE if LATEST_PROFILE else {"name": "Guest", "phone": None, "email": None}

    session = {
        "booking_state": None,
        "booking_data": {},
        "reschedule_state": None,
        "reschedule_data": {},
        "clinic_refresh_token": refresh_token,
        "user_profile": profile,
        "patient_name": profile.get("name"),
        "patient_phone": profile.get("phone"),
        "payment_status": None,        # None → "pending" → "completed"
        "payment_session_id": None,
        "language": "hi",               # "hi" = Hinglish, "en" = plain English (iOS)
    }

    print("🔐 SESSION:", profile)

    try:
        while True:
            raw = await websocket.receive_text()
            print(f"⬅️ RECV: {raw}")

            try:
                payload = json.loads(raw)
            except Exception as e:
                print(f"JSON parse error: {e}")
                continue

            # ── Update profile ──
            incoming_profile = payload.get("user_profile")
            if incoming_profile and incoming_profile.get("name"):
                session["user_profile"] = incoming_profile
                session["patient_name"] = incoming_profile.get("name")
                session["patient_phone"] = incoming_profile.get("phone")

            # Update language preference if sent by frontend
            incoming_lang = payload.get("language")
            if incoming_lang in ("hi", "en"):
                session["language"] = incoming_lang

            user_input = payload.get("user_input", "").strip()
            if not user_input:
                continue

            # ================================================================
            # PAYMENT GATE
            # When payment_status == "pending", ONLY accept:
            #   "paid"              → verify and confirm booking
            #   "payment_cancelled" → end the call
            # Everything else is SILENTLY DROPPED.
            # ================================================================
            if session.get("payment_status") == "pending":

                if user_input.lower() == "payment_cancelled":
                    print("❌ Payment cancelled by user — ending call")
                    await websocket.send_json({
                        "type": "call_end",
                        "message": "Payment cancel ho gayi. Aapka slot release ho gaya. Phir se book karne ke liye call karein."
                    })
                    break  # exit the loop → triggers cleanup

                if user_input.lower() == "paid":
                    print("💳 Verifying Stripe payment...")
                    paid = await verify_stripe_payment(session.get("payment_session_id"))

                    if paid:
                        session["payment_status"] = "completed"
                        session["booking_state"] = "confirm_booking"

                        await websocket.send_json({
                            "response": "Payment verified ✅ Aapka appointment confirm ho raha hai..."
                        })

                        try:
                            response = await route_intent(
                                intent="booking",
                                text="confirm booking",
                                session=session,
                                language=session.get("language", "hi")
                            )
                            if not response:
                                response = "Aapka appointment book ho gaya. Shukriya!"
                            await websocket.send_json({"response": response})
                        except Exception as e:
                            print(f"❌ Booking confirm error: {e}")
                            import traceback; traceback.print_exc()
                            await websocket.send_json({
                                "response": "Payment complete hai! Lekin appointment confirm karne mein dikkat aayi. Clinic ko call karein."
                            })
                    else:
                        await websocket.send_json({
                            "response": "Payment abhi complete nahi hui. Please Stripe mein payment karein phir wapas aayein."
                    })

                else:
                    # ✅ SILENTLY DROP all other messages during payment
                    print(f"🔕 Dropping during payment: '{user_input}'")

                continue  # always skip normal flow when payment pending

            # ================================================================
            # NORMAL INTENT FLOW
            # ================================================================
            force_process = (
                session.get("booking_state") == "awaiting_slot" or
                session.get("reschedule_state") is not None
            )

            if force_process or user_input.endswith((".", "?", "!")) or len(user_input) > 15:
                try:
                    intent = classify_intent(user_input)
                    print(f"🤖 intent='{intent}' | patient='{session['patient_name']}'")

                    response = await route_intent(intent=intent, text=user_input, session=session, language=session.get("language", "hi"))

                    if response is None:
                        response = "Sorry, kuch samajh nahi aaya. Please phir se bolein."

                    # ── Payment gate: slot just selected ──
                    if (
                        session.get("booking_state") == "slot_selected" and
                        session.get("payment_status") is None
                    ):
                        print("💳 Slot selected — creating Stripe session...")
                        session["payment_status"] = "pending"

                        stripe_result = await create_stripe_checkout(frontend_url)

                        if stripe_result["ok"]:
                            session["payment_session_id"] = stripe_result["session_id"]

                            slot_msg = response
                            if isinstance(response, dict):
                                slot_msg = (
                                    response.get("message") or
                                    response.get("text") or
                                    "Slot select ho gaya."
                                )

                            print(f"💳 Sending payment_required | url={stripe_result['url'][:60]}...")
                            await websocket.send_json({
                                "type": "payment_required",
                                "response": slot_msg,
                                "checkout_url": stripe_result["url"],
                                "message": f"{slot_msg} Ab ₹500 booking fee pay karein.",
                            })
                        else:
                            print(f"❌ Stripe failed: {stripe_result['error']}")
                            session["payment_status"] = None
                            await websocket.send_json({
                                "response": "Payment gateway abhi available nahi hai. Thodi der baad try karein."
                            })

                        continue

                    await websocket.send_json({"response": response})

                except Exception as e:
                    print(f"❌ ROUTING ERROR: {e}")
                    import traceback; traceback.print_exc()
                    await websocket.send_json({"response": "Kuch problem aayi. Please phir se bolein."})

    except WebSocketDisconnect:
        print(f"🔌 Disconnected: {client_id}")
    except Exception as e:
        print(f"💀 CRITICAL: {e}")
        import traceback; traceback.print_exc()
    finally:
        remove_active_call(client_id)
        next_client = pop_next_from_queue()
        if next_client:
            print(f"🚀 Queue promoted: {next_client}")