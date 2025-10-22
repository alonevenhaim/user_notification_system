import asyncio
import grpc
import os
import sys

# Get the directory of the current script
# Falls back to the current working directory if __file__ is not available
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # Fallback when __file__ is not defined
    script_dir = os.getcwd()

# Add the src directory to Python path so we can import modules from there
src_path = os.path.join(script_dir, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Now import from the src directory
from notification_service_pb2 import SendMessageRequest, MessageType
from notification_service_pb2_grpc import NotificationServiceStub, add_NotificationServiceServicer_to_server
from server import NotificationServiceImpl

PORT = 50053

async def start_server() -> grpc.aio.Server:
    server = grpc.aio.server()
    add_NotificationServiceServicer_to_server(NotificationServiceImpl(), server)
    server.add_insecure_port(f"[::]:{PORT}")
    await server.start()
    return server

async def run_demo():
    print(f"Starting demo client on port {PORT}...")
    
    # Use async context manager so the channel is closed cleanly
    async with grpc.aio.insecure_channel(f"localhost:{PORT}") as channel:
        stub = NotificationServiceStub(channel)
        
        # Create a proper request message
        request = SendMessageRequest(
            client_id="demo_client_1",
            message_type=MessageType.HELLO
        )
        
        # Send the message
        response = await stub.SendMessage(request)
        assert response.success, f"Failed: {response.message}"
        print(f"✓ Hello message sent: {response.message}")
        
        # Check status
        from notification_service_pb2 import GetClientStatusRequest
        status_request = GetClientStatusRequest(client_id="demo_client_1")
        status_response = await stub.GetClientStatus(status_request)
        print(f"✓ Client status: {dict(status_response.client_statuses)}")
        
        # Send goodbye message
        goodbye_request = SendMessageRequest(
            client_id="demo_client_1",
            message_type=MessageType.GOODBYE
        )
        goodbye_response = await stub.SendMessage(goodbye_request)
        print(f"✓ Goodbye message sent: {goodbye_response.message}")
        
        # Check final status
        final_status_response = await stub.GetClientStatus(status_request)
        print(f"✓ Final status: {dict(final_status_response.client_statuses)}")

async def main():
    server = await start_server()
    print(f"Server started on port {PORT}")
    
    # Give server a moment to fully start
    await asyncio.sleep(0.5)
    
    try:
        await run_demo()
        print("\n✅ Demo completed successfully!")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Allow in-flight RPCs to finish; adjust grace as you like
        print("\nShutting down server...")
        await server.stop(grace=2)
        # Wait until server is fully terminated before loop ends
        await server.wait_for_termination()
        print("Server stopped.")

if __name__ == "__main__":
    asyncio.run(main())
