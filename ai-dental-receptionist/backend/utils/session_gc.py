import asyncio
from datetime import datetime


async def session_gc_loop():
    """
    Session garbage collection loop - runs every 60 seconds
    Cleans up expired sessions from memory
    """
    print("🟢 Session GC Loop starting...")
    iteration = 0

    while True:
        try:
            iteration += 1

            # ✅ FIXED IMPORT (absolute, correct root)
            from backend.core.conversation_manager import cleanup_expired_sessions

            cleaned_count = cleanup_expired_sessions()

            timestamp = datetime.utcnow().isoformat()
            if cleaned_count > 0:
                print(
                    f"[{timestamp}] 🧹 GC #{iteration}: "
                    f"Cleaned up {cleaned_count} expired session(s)"
                )
            else:
                print(
                    f"[{timestamp}] ✅ GC #{iteration}: No expired sessions"
                )

            await asyncio.sleep(60)

        except asyncio.CancelledError:
            print("🛑 Session GC Loop cancelled (shutdown)")
            break

        except Exception as e:
            print(f"❌ Error in session GC loop: {e}")
            await asyncio.sleep(60)


async def manual_cleanup():
    """Manually trigger session cleanup (for testing)"""
    from backend.core.conversation_manager import cleanup_expired_sessions

    print("🧹 Running manual session cleanup...")
    count = cleanup_expired_sessions()
    print(f"✅ Cleaned up {count} sessions")
    return count
