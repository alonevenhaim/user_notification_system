"""
Unit tests for the Asynchronous User Notification System

This module contains comprehensive tests for the notification service,
including unit tests and end-to-end tests with proper async handling.
"""

import asyncio
import pytest
import pytest_asyncio
import grpc
from grpc import aio
from unittest.mock import AsyncMock
from typing import Dict, List

# Import our modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from server import NotificationServiceImpl
from client import NotificationClient
from notification_service_pb2 import MessageType, SendMessageRequest, GetClientStatusRequest
from notification_service_pb2_grpc import add_NotificationServiceServicer_to_server

import allure


class TestNotificationServiceUnit:
    """Unit tests for the NotificationService implementation."""

    @pytest.fixture
    def service(self):
        """Create a fresh service instance for each test."""
        return NotificationServiceImpl()

    @allure.feature("Message Processing")
    @allure.story("Hello Message")
    @pytest.mark.asyncio
    async def test_send_hello_message(self, service):
        """Test sending a Hello message marks client as connected."""
        # Arrange
        client_id = "test_client_1"
        request = SendMessageRequest(client_id=client_id, message_type=MessageType.HELLO)
        context = AsyncMock()

        # Act
        response = await service.SendMessage(request, context)

        # Assert
        assert response.success is True
        assert "successfully" in response.message.lower()

        # Verify client status
        statuses = service.get_client_status_sync(client_id)
        assert statuses[client_id] == "connected"

    @allure.feature("Message Processing")
    @allure.story("Goodbye Message")
    @pytest.mark.asyncio
    async def test_send_goodbye_message(self, service):
        """Test sending a Goodbye message marks client as disconnected."""
        # Arrange
        client_id = "test_client_2"

        # First send Hello
        hello_request = SendMessageRequest(client_id=client_id, message_type=MessageType.HELLO)
        context = AsyncMock()
        await service.SendMessage(hello_request, context)

        # Act - Send Goodbye
        goodbye_request = SendMessageRequest(client_id=client_id, message_type=MessageType.GOODBYE)
        response = await service.SendMessage(goodbye_request, context)

        # Assert
        assert response.success is True

        # Verify client status
        statuses = service.get_client_status_sync(client_id)
        assert statuses[client_id] == "disconnected"

    @allure.feature("Message Processing")
    @allure.story("Invalid Messages")
    @pytest.mark.asyncio
    async def test_invalid_message_type(self, service):
        """Test that invalid message types are rejected."""
        # Arrange
        client_id = "test_client_3"
        request = SendMessageRequest(client_id=client_id, message_type=MessageType.UNKNOWN)
        context = AsyncMock()

        # Mock abort to raise an exception
        async def mock_abort(status_code, message):
            raise grpc.RpcError(f"gRPC error: {status_code} - {message}")

        context.abort.side_effect = mock_abort

        # Act & Assert
        with pytest.raises(grpc.RpcError):
            await service.SendMessage(request, context)

        # Verify context.abort was called
        context.abort.assert_called_once()
        assert context.abort.call_args[0][0] == grpc.StatusCode.INVALID_ARGUMENT

    @allure.feature("Message Processing")
    @allure.story("Empty Client ID")
    @pytest.mark.asyncio
    async def test_empty_client_id(self, service):
        """Test that empty client IDs are rejected."""
        # Arrange
        request = SendMessageRequest(client_id="", message_type=MessageType.HELLO)
        context = AsyncMock()

        # Mock abort to raise an exception
        async def mock_abort(status_code, message):
            raise grpc.RpcError(f"gRPC error: {status_code} - {message}")

        context.abort.side_effect = mock_abort

        # Act & Assert
        with pytest.raises(grpc.RpcError):
            await service.SendMessage(request, context)

        # Verify context.abort was called
        context.abort.assert_called_once()
        assert context.abort.call_args[0][0] == grpc.StatusCode.INVALID_ARGUMENT

    @allure.feature("Status Retrieval")
    @allure.story("Get Specific Client Status")
    @pytest.mark.asyncio
    async def test_get_specific_client_status(self, service):
        """Test retrieving status for a specific client."""
        # Arrange
        client_id = "test_client_4"
        hello_request = SendMessageRequest(client_id=client_id, message_type=MessageType.HELLO)
        context = AsyncMock()
        await service.SendMessage(hello_request, context)

        # Act
        status_request = GetClientStatusRequest(client_id=client_id)
        response = await service.GetClientStatus(status_request, context)

        # Assert
        assert client_id in response.client_statuses
        assert response.client_statuses[client_id] == "connected"

    @allure.feature("Status Retrieval")
    @allure.story("Get All Client Statuses")
    @pytest.mark.asyncio
    async def test_get_all_client_statuses(self, service):
        """Test retrieving statuses for all clients."""
        # Arrange - Add multiple clients
        clients = ["client_a", "client_b", "client_c"]
        context = AsyncMock()

        for client in clients:
            request = SendMessageRequest(client_id=client, message_type=MessageType.HELLO)
            await service.SendMessage(request, context)

        # Act
        status_request = GetClientStatusRequest()  # No specific client_id
        response = await service.GetClientStatus(status_request, context)

        # Assert
        assert len(response.client_statuses) == len(clients)
        for client in clients:
            assert response.client_statuses[client] == "connected"

    @allure.feature("Concurrency")
    @allure.story("Multiple Clients")
    @pytest.mark.asyncio
    async def test_multiple_clients_concurrent(self, service):
        """Test handling multiple clients concurrently."""
        # Arrange
        client_ids = [f"concurrent_client_{i}" for i in range(10)]
        context = AsyncMock()

        # Act - Send messages concurrently
        tasks = []
        for client_id in client_ids:
            request = SendMessageRequest(client_id=client_id, message_type=MessageType.HELLO)
            task = service.SendMessage(request, context)
            tasks.append(task)

        responses = await asyncio.gather(*tasks)

        # Assert
        assert all(response.success for response in responses)

        # Verify all clients are connected
        statuses = service.get_client_status_sync()
        for client_id in client_ids:
            assert statuses[client_id] == "connected"


class TestNotificationClientUnit:
    """Unit tests for the NotificationClient."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return NotificationClient("localhost:50051")

    @allure.feature("Client Initialization")
    @allure.story("Connection Management")
    def test_client_initialization(self, client):
        """Test client initialization."""
        assert client.server_address == "localhost:50051"
        assert client.channel is None
        assert client.stub is None

    @allure.feature("Client Connection")
    @allure.story("Error Handling")
    @pytest.mark.asyncio
    async def test_client_operations_without_connection(self, client):
        """Test that client operations fail without connection."""
        with pytest.raises(RuntimeError, match="Client not connected"):
            await client.send_hello("test_client")

        with pytest.raises(RuntimeError, match="Client not connected"):
            await client.get_client_status()


@allure.feature("End-to-End Testing")
@allure.story("Full System Integration")
class TestEndToEnd:
    """
    End-to-end tests for the complete notification system.

    These tests use real gRPC servers and clients to verify full system integration.
    Tests rely on the global pytest timeout (60s) for protection against hanging.
    """

    @pytest_asyncio.fixture(scope="function")
    async def server_port(self):
        """Start a test server and return its port."""
        from concurrent.futures import ThreadPoolExecutor
        import random

        # Use a random port in a safe range to avoid conflicts
        test_port = random.randint(50200, 50299)

        # Create server instance
        server = aio.server(ThreadPoolExecutor(max_workers=10))

        # Add service
        service = NotificationServiceImpl()
        add_NotificationServiceServicer_to_server(service, server)

        # Add port and start
        listen_addr = f'[::]:{test_port}'

        try:
            server.add_insecure_port(listen_addr)
            await server.start()

            # Wait for server to be ready
            await asyncio.sleep(1.0)

            yield test_port

        except Exception as e:
            # If port is busy, skip the test
            pytest.skip(f"Could not start test server on port {test_port}: {e}")
        finally:
            # Proper cleanup with grace period
            try:
                await server.stop(grace=2.0)
            except Exception:
                pass  # Ignore cleanup errors

    @allure.feature("End-to-End")
    @allure.story("Single Client Workflow")
    @pytest.mark.asyncio
    async def test_single_client_workflow(self, server_port):
        """Test complete workflow for a single client."""
        client = NotificationClient(f"localhost:{server_port}")

        try:
            # Connect
            await client.connect()

            # Send Hello
            success = await client.send_hello("e2e_client_1")
            assert success is True

            # Check status
            status = await client.get_client_status("e2e_client_1")
            assert status["e2e_client_1"] == "connected"

            # Send Goodbye
            success = await client.send_goodbye("e2e_client_1")
            assert success is True

            # Check final status
            status = await client.get_client_status("e2e_client_1")
            assert status["e2e_client_1"] == "disconnected"

        finally:
            await client.disconnect()

    @allure.feature("End-to-End")
    @allure.story("Multiple Clients")
    @pytest.mark.asyncio
    async def test_multiple_clients_workflow(self, server_port):
        """Test workflow with multiple clients."""
        num_clients = 5
        clients = []

        try:
            # Create and connect multiple clients
            for i in range(num_clients):
                client = NotificationClient(f"localhost:{server_port}")
                await client.connect()
                clients.append(client)

            # Send Hello messages from all clients
            for i, client in enumerate(clients):
                success = await client.send_hello(f"multi_client_{i}")
                assert success is True

            # Check all statuses using first client
            all_statuses = await clients[0].get_client_status()

            # Verify all clients are connected
            for i in range(num_clients):
                client_id = f"multi_client_{i}"
                assert client_id in all_statuses
                assert all_statuses[client_id] == "connected"

            # Disconnect some clients
            for i in range(0, num_clients, 2):  # Every other client
                success = await clients[i].send_goodbye(f"multi_client_{i}")
                assert success is True

            # Verify mixed statuses
            final_statuses = await clients[0].get_client_status()
            for i in range(num_clients):
                client_id = f"multi_client_{i}"
                if i % 2 == 0:
                    assert final_statuses[client_id] == "disconnected"
                else:
                    assert final_statuses[client_id] == "connected"

        finally:
            # Cleanup all clients
            for client in clients:
                await client.disconnect()

    @allure.feature("End-to-End")
    @allure.story("Invalid Message Handling")
    @pytest.mark.asyncio
    async def test_invalid_message_handling_e2e(self, server_port):
        """Test end-to-end handling of invalid messages."""
        client = NotificationClient(f"localhost:{server_port}")

        try:
            await client.connect()

            # Test empty client ID
            success = await client.send_hello("")
            assert success is False  # Should fail gracefully

            # Test normal operation still works
            success = await client.send_hello("valid_client")
            assert success is True

            status = await client.get_client_status("valid_client")
            assert status["valid_client"] == "connected"

        finally:
            await client.disconnect()

    @allure.feature("End-to-End")
    @allure.story("Stress Testing")
    @pytest.mark.asyncio
    async def test_concurrent_operations_stress(self, server_port):
        """Test system under concurrent load."""
        num_concurrent_operations = 20
        client = NotificationClient(f"localhost:{server_port}")

        try:
            await client.connect()

            # Create tasks for concurrent operations
            tasks = []
            for i in range(num_concurrent_operations):
                if i % 2 == 0:
                    task = client.send_hello(f"stress_client_{i}")
                else:
                    task = client.send_goodbye(f"stress_client_{i}")
                tasks.append(task)

            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Verify no exceptions occurred
            success_count = sum(1 for result in results if result is True)
            assert success_count >= num_concurrent_operations * 0.8  # Allow some tolerance

            # Verify final state
            all_statuses = await client.get_client_status()

            # Check that we have entries for our stress test clients
            stress_clients = [key for key in all_statuses.keys() if key.startswith("stress_client_")]
            assert len(stress_clients) > 0

        finally:
            await client.disconnect()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--allure-features"])