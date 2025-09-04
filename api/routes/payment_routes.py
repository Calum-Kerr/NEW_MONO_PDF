from flask import Blueprint, request, jsonify, current_app
from core.payments import StripeManager
from core.storage import validate_session

bp = Blueprint('payments', __name__)
stripe_manager = StripeManager()

@bp.route('/create-checkout-session', methods=['POST'])
@validate_session
def create_checkout_session():
    """Create Stripe checkout session for subscription"""
    try:
        data = request.get_json()
        
        if not data.get('price_id'):
            return jsonify({'error': 'Price ID is required'}), 400
        
        user = request.current_user
        
        result = stripe_manager.create_checkout_session(
            user_id=user['id'],
            user_email=user['email'],
            price_id=data['price_id'],
            success_url=data.get('success_url'),
            cancel_url=data.get('cancel_url')
        )
        
        if result['success']:
            return jsonify({
                'checkout_url': result['checkout_url'],
                'session_id': result['session_id']
            }), 200
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        current_app.logger.error(f"Checkout session error: {str(e)}")
        return jsonify({'error': 'Failed to create checkout session'}), 500

@bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks"""
    try:
        payload = request.get_data()
        sig_header = request.headers.get('Stripe-Signature')
        
        result = stripe_manager.handle_webhook(payload, sig_header)
        
        if result['success']:
            return jsonify({'received': True}), 200
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        current_app.logger.error(f"Webhook error: {str(e)}")
        return jsonify({'error': 'Webhook processing failed'}), 500

@bp.route('/subscription/cancel', methods=['POST'])
@validate_session
def cancel_subscription():
    """Cancel user's subscription"""
    try:
        user = request.current_user
        
        result = stripe_manager.cancel_subscription(user['id'])
        
        if result['success']:
            return jsonify({'message': 'Subscription cancelled successfully'}), 200
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        current_app.logger.error(f"Subscription cancellation error: {str(e)}")
        return jsonify({'error': 'Failed to cancel subscription'}), 500

@bp.route('/subscription/status', methods=['GET'])
@validate_session
def get_subscription_status():
    """Get user's subscription status"""
    try:
        user = request.current_user
        
        result = stripe_manager.get_subscription_status(user['id'])
        
        if result['success']:
            return jsonify({
                'subscription': result['subscription'],
                'usage': result['usage']
            }), 200
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        current_app.logger.error(f"Subscription status error: {str(e)}")
        return jsonify({'error': 'Failed to get subscription status'}), 500

@bp.route('/usage', methods=['GET'])
@validate_session
def get_usage():
    """Get user's current usage statistics"""
    try:
        user = request.current_user
        
        result = stripe_manager.get_usage_stats(user['id'])
        
        if result['success']:
            return jsonify(result['usage']), 200
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        current_app.logger.error(f"Usage stats error: {str(e)}")
        return jsonify({'error': 'Failed to get usage statistics'}), 500