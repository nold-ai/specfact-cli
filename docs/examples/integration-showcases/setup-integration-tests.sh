#!/bin/bash
# setup-integration-tests.sh
# Quick setup script for integration showcase testing
#
# Usage:
#   From specfact-cli repo root:
#     ./docs/examples/integration-showcases/setup-integration-tests.sh
#
#   Or from this directory:
#     ./setup-integration-tests.sh
#
# Prerequisites:
#   - Python 3.11+ (required by specfact-cli)
#   - pip install specfact-cli (for interactive AI assistant mode)
#   - pip install semgrep (optional, for async pattern detection in Example 1)
#   - specfact init (one-time IDE setup)
#
# This script creates test cases in /tmp/specfact-integration-tests/ for
# validating the integration showcase examples.
#
# Project Structure Created:
#   - All examples use src/ directory for source code (required for specfact repro)
#   - tests/ directory created for test files
#   - tools/semgrep/ directory created for Example 1 (Semgrep async config copied if available)

set -e

BASE_DIR="/tmp/specfact-integration-tests"
echo "📁 Creating test directory: $BASE_DIR"
mkdir -p "$BASE_DIR"
cd "$BASE_DIR"

# Example 1: VS Code Integration
echo "📝 Setting up Example 1: VS Code Integration"
mkdir -p example1_vscode/src example1_vscode/tests example1_vscode/tools/semgrep
cd example1_vscode
git init > /dev/null 2>&1 || true

# Copy Semgrep config if available from specfact-cli repo
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
if [ -f "$REPO_ROOT/src/specfact_cli/resources/semgrep/async.yml" ]; then
    cp "$REPO_ROOT/src/specfact_cli/resources/semgrep/async.yml" tools/semgrep/ 2>/dev/null || true
    echo "✅ Copied Semgrep async config"
elif [ -f "$REPO_ROOT/tools/semgrep/async.yml" ]; then
    cp "$REPO_ROOT/tools/semgrep/async.yml" tools/semgrep/ 2>/dev/null || true
    echo "✅ Copied Semgrep async config"
else
    echo "⚠️  Semgrep config not found - creating minimal config"
    # Create minimal Semgrep config for async detection
    cat > tools/semgrep/async.yml << 'SEMGREP_EOF'
rules:
  - id: blocking-io-in-async
    pattern: |
      def $FUNC(...):
        ...
        $CALL(...)
    message: Blocking I/O call in potentially async context
    languages: [python]
    severity: ERROR
SEMGREP_EOF
    echo "✅ Created minimal Semgrep async config"
fi

# Check if semgrep is installed, offer to install if not
if ! command -v semgrep &> /dev/null; then
    echo "⚠️  Semgrep not found in PATH"
    echo "   To enable async pattern detection, install Semgrep:"
    echo "   pip install semgrep"
    echo "   (This is optional - async detection will be skipped if Semgrep is not installed)"
else
    echo "✅ Semgrep found: $(semgrep --version | head -1)"
fi

cat > src/views.py << 'EOF'
# views.py - Legacy Django view with async bug
"""Payment processing views for legacy Django application."""

from typing import Dict, Any

class PaymentView:
    """Legacy Django view being modernized to async.
    
    This view handles payment processing operations including
    creating payments, checking status, and cancelling payments.
    """
    
    def process_payment(self, request):
        """Process payment with blocking I/O call.
        
        This method processes a payment request and sends a notification.
        The send_notification call is blocking and should be async.
        """
        user = get_user(request.user_id)
        payment = create_payment(user.id, request.amount)
        send_notification(user.email, payment.id)  # ⚠️ Blocking call in async context
        return {"status": "success"}
    
    def get_payment_status(self, payment_id: str) -> dict:
        """Get payment status by ID.
        
        Returns the current status of a payment.
        """
        return {"id": payment_id, "status": "pending"}
    
    def cancel_payment(self, payment_id: str) -> dict:
        """Cancel a payment.
        
        Cancels an existing payment and returns the updated status.
        """
        return {"id": payment_id, "status": "cancelled"}
    
    def create_payment(self, user_id: str, amount: float) -> dict:
        """Create a new payment.
        
        Creates a new payment record for the specified user and amount.
        """
        return {"id": "123", "user_id": user_id, "amount": amount}
EOF
echo "✅ Example 1 setup complete (src/views.py created)"
cd ..

# Example 2: Cursor Integration
echo "📝 Setting up Example 2: Cursor Integration"
mkdir -p example2_cursor/src example2_cursor/tests
cd example2_cursor
git init > /dev/null 2>&1 || true
cat > src/pipeline.py << 'EOF'
# pipeline.py - Legacy data processing
class DataProcessor:
    """Processes data with None value handling.
    
    This processor handles data transformation and validation,
    with special attention to None value handling for legacy data.
    """
    
    def process_data(self, data: list[dict]) -> dict:
        """Process data with critical None handling.
        
        Processes a list of data dictionaries, filtering out None values
        and calculating totals. Critical for handling legacy data formats.
        """
        if not data:
            return {"status": "empty", "count": 0}
        
        # Critical: handles None values in data
        filtered = [d for d in data if d is not None and d.get("value") is not None]
        
        if len(filtered) == 0:
            return {"status": "no_valid_data", "count": 0}
        
        return {
            "status": "success",
            "count": len(filtered),
            "total": sum(d["value"] for d in filtered)
        }
    
    def validate_data(self, data: list[dict]) -> bool:
        """Validate data structure.
        
        Checks if data is a non-empty list of dictionaries.
        """
        return isinstance(data, list) and len(data) > 0
    
    def transform_data(self, data: list[dict]) -> list[dict]:
        """Transform data format.
        
        Transforms data by adding a processed flag to each item.
        """
        return [{"processed": True, **item} for item in data if item]
    
    def filter_data(self, data: list[dict], key: str) -> list[dict]:
        """Filter data by key.
        
        Returns only items that contain the specified key.
        """
        return [item for item in data if key in item]
EOF
echo "✅ Example 2 setup complete (src/pipeline.py created)"
cd ..

# Example 3: GitHub Actions Integration
echo "📝 Setting up Example 3: GitHub Actions Integration"
mkdir -p example3_github_actions/src example3_github_actions/tests
cd example3_github_actions
git init > /dev/null 2>&1 || true
cat > src/api.py << 'EOF'
# api.py - New endpoint with type mismatch
class UserAPI:
    """User API endpoints.
    
    Provides REST API endpoints for user management operations
    including profile retrieval, statistics, and updates.
    """
    
    def get_user_stats(self, user_id: str) -> dict:
        """Get user statistics.
        
        Returns user statistics as a dictionary. Note: This method
        has a type mismatch bug - returns int instead of dict.
        """
        # Simulate: calculate_stats returns int, not dict
        stats = 42  # Returns int, not dict
        return stats  # ⚠️ Type mismatch: int vs dict
    
    def get_user_profile(self, user_id: str) -> dict:
        """Get user profile information.
        
        Retrieves the complete user profile for the given user ID.
        """
        return {"id": user_id, "name": "John Doe"}
    
    def update_user(self, user_id: str, data: dict) -> dict:
        """Update user information.
        
        Updates user information with the provided data.
        """
        return {"id": user_id, "updated": True, **data}
    
    def create_user(self, user_data: dict) -> dict:
        """Create a new user.
        
        Creates a new user with the provided data.
        """
        return {"id": "new-123", **user_data}
EOF
echo "✅ Example 3 setup complete (src/api.py created)"
cd ..

# Example 4: Pre-commit Hook
echo "📝 Setting up Example 4: Pre-commit Hook"
mkdir -p example4_precommit/src example4_precommit/tests
cd example4_precommit
git init > /dev/null 2>&1 || true
cat > src/legacy.py << 'EOF'
# legacy.py - Original function
class OrderProcessor:
    """Processes orders.
    
    Handles order processing operations including order creation,
    status retrieval, and order updates.
    """
    
    def process_order(self, order_id: str) -> dict:
        """Process an order.
        
        Processes an order and returns its status.
        """
        return {"order_id": order_id, "status": "processed"}
    
    def get_order(self, order_id: str) -> dict:
        """Get order details.
        
        Retrieves order information by order ID.
        """
        return {"id": order_id, "items": []}
    
    def update_order(self, order_id: str, data: dict) -> dict:
        """Update an order.
        
        Updates order information with the provided data.
        """
        return {"id": order_id, "updated": True, **data}
EOF
cat > src/caller.py << 'EOF'
# caller.py - Uses legacy function
from legacy import OrderProcessor

processor = OrderProcessor()
result = processor.process_order(order_id="123")
EOF
# Create pre-commit hook (enforcement must be configured separately)
mkdir -p .git/hooks
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/sh
specfact --no-banner plan compare --code-vs-plan
EOF
chmod +x .git/hooks/pre-commit
echo "⚠️  Pre-commit hook created. Remember to run 'specfact enforce stage --preset balanced' before testing."
echo "✅ Example 4 setup complete (src/legacy.py, src/caller.py, pre-commit hook created)"
cd ..

# Example 5: Agentic Workflow
echo "📝 Setting up Example 5: Agentic Workflow"
mkdir -p example5_agentic/src example5_agentic/tests
cd example5_agentic
git init > /dev/null 2>&1 || true
cat > src/validator.py << 'EOF'
# validator.py - AI-generated validation with edge case
class DataValidator:
    """Validates and calculates data.
    
    Provides validation and calculation utilities for data processing,
    with support for various data types and formats.
    """
    
    def validate_and_calculate(self, data: dict) -> float:
        """Validate data and perform calculation.
        
        Validates input data and performs division calculation.
        Note: This method has an edge case bug - divisor could be 0.
        """
        value = data.get("value", 0)
        divisor = data.get("divisor", 1)
        return value / divisor  # ⚠️ Edge case: divisor could be 0
    
    def validate_input(self, data: dict) -> bool:
        """Validate input data structure.
        
        Checks if data is a valid dictionary with required fields.
        """
        return isinstance(data, dict) and "value" in data
    
    def calculate_total(self, values: list[float]) -> float:
        """Calculate total from list of values.
        
        Sums all values in the provided list.
        """
        return sum(values) if values else 0.0
    
    def check_data_quality(self, data: dict) -> bool:
        """Check data quality.
        
        Performs quality checks on the provided data dictionary.
        """
        return isinstance(data, dict) and len(data) > 0
EOF
echo "✅ Example 5 setup complete (src/validator.py created)"
cd ..

echo ""
echo "✅ All test cases created in $BASE_DIR"
echo ""
echo "📋 Test directories:"
echo "  1. example1_vscode       - VS Code async bug detection"
echo "  2. example2_cursor        - Cursor regression prevention"
echo "  3. example3_github_actions - GitHub Actions type error"
echo "  4. example4_precommit     - Pre-commit breaking change"
echo "  5. example5_agentic       - Agentic workflow edge case"
echo ""
echo "⚠️  IMPORTANT: For Interactive AI Assistant Usage"
echo ""
echo "   Before using slash commands in your IDE, you need to:"
echo "   1. Install SpecFact via pip: pip install specfact-cli"
echo "   2. Initialize IDE integration (one-time per project):"
echo "      cd $BASE_DIR/example1_vscode"
echo "      specfact init"
echo ""
echo "   This sets up prompt templates so slash commands work."
echo ""
echo "🚀 Next steps:"
echo "  1. Follow the testing guide: integration-showcases-testing-guide.md (in this directory)"
echo "  2. Install SpecFact: pip install specfact-cli"
echo "  3. Initialize IDE: cd $BASE_DIR/example1_vscode && specfact init"
echo "  4. Open test file in IDE and use slash command: /specfact-import-from-code"
echo "     (Interactive mode automatically uses IDE workspace - no --repo . needed)"
echo ""
echo "📚 Documentation:"
echo "   - Testing Guide: docs/examples/integration-showcases/integration-showcases-testing-guide.md"
echo "   - Quick Reference: docs/examples/integration-showcases/integration-showcases-quick-reference.md"
echo "   - Showcases: docs/examples/integration-showcases/integration-showcases.md"
echo ""

