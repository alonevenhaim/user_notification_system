"""
Simple integration test for the Notification System

This test demonstrates the system working correctly with a simpler approach.
"""

import asyncio
import pytest
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from server import NotificationServiceImpl
from notification_service_pb2 import MessageType, SendMessageRequest, GetClientStatusRequest
from unittest.mock import AsyncMock


@pytest.mark.asyncio
async def test_complete_workflow():
    """Test the complete workflow of the notification system."""
    # Create service instance
    service = NotificationServiceImpl()
    context = AsyncMock()
    
    # Test Hello message
    hello_request = SendMessageRequest(
        client_id="integration_test_client",
        message_type=MessageType.HELLO
    )
    
    response = await service.SendMessage(hello_request, context)
    assert response.success is True
    assert "successfully" in response.message.lower()
    
    # Verify client is connected
    status_request = GetClientStatusRequest(client_id="integration_test_client")
    status_response = await service.GetClientStatus(status_request, context)
    
    assert "integration_test_client" in status_response.client_statuses
    assert status_response.client_statuses["integration_test_client"] == "connected"
    
    # Test Goodbye message
    goodbye_request = SendMessageRequest(
        client_id="integration_test_client",
        message_type=MessageType.GOODBYE
    )
    
    response = await service.SendMessage(goodbye_request, context)
    assert response.success is True
    
    # Verify client is disconnected
    status_response = await service.GetClientStatus(status_request, context)
    assert status_response.client_statuses["integration_test_client"] == "disconnected"
    
    print("✅ Complete workflow test passed!")


@pytest.mark.asyncio 
async def test_multiple_clients():
    """Test multiple clients interacting with the system."""
    service = NotificationServiceImpl()
    context = AsyncMock()
    
    clients = ["client_1", "client_2", "client_3"]
    
    # All clients say hello
    for client_id in clients:
        request = SendMessageRequest(
            client_id=client_id,
            message_type=MessageType.HELLO
        )
        response = await service.SendMessage(request, context)
        assert response.success is True
    
    # Check all statuses
    status_request = GetClientStatusRequest()  # Get all clients
    status_response = await service.GetClientStatus(status_request, context)
    
    assert len(status_response.client_statuses) >= len(clients)
    for client_id in clients:
        assert status_response.client_statuses[client_id] == "connected"
    
    # Some clients say goodbye
    for i, client_id in enumerate(clients):
        if i % 2 == 0:  # Every other client
            request = SendMessageRequest(
                client_id=client_id,
                message_type=MessageType.GOODBYE
            )
            response = await service.SendMessage(request, context)
            assert response.success is True
    
    # Check final statuses
    status_response = await service.GetClientStatus(status_request, context)
    for i, client_id in enumerate(clients):
        if i % 2 == 0:
            assert status_response.client_statuses[client_id] == "disconnected"
        else:
            assert status_response.client_statuses[client_id] == "connected"
    
    print("✅ Multiple clients test passed!")


if __name__ == "__main__":
    asyncio.run(test_complete_workflow())
    asyncio.run(test_multiple_clients())
    print("🎉 All integration tests passed!")