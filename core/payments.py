"""
Stripe payment integration for PDF tools platform.
Handles subscriptions, webhooks, and payment processing.
"""

import os
import stripe
import hmac
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from supabase import create_client, Client

class PaymentManager:
    def __init__(self):
        self.stripe_secret_key = os.getenv('STRIPE_SECRET_KEY')
        self.stripe_webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not all([self.stripe_secret_key, self.supabase_url, self.service_key]):
            raise ValueError("Missing payment configuration")
        
        stripe.api_key = self.stripe_secret_key
        self.supabase: Client = create_client(self.supabase_url, self.service_key)
        
        # Subscription plans
        self.plans = {
            'pro_monthly': {
                'name': 'Pro Monthly',
                'price_id': os.getenv('STRIPE_PRO_MONTHLY_PRICE_ID'),
                'tier': 'pro',
                'features': [
                    'Unlimited PDF operations',
                    'Advanced tools (OCR, compression)',
                    'Priority processing',
                    'Email support'
                ]
            },
            'pro_yearly': {
                'name': 'Pro Yearly',
                'price_id': os.getenv('STRIPE_PRO_YEARLY_PRICE_ID'),
                'tier': 'pro',
                'features': [
                    'Unlimited PDF operations',
                    'Advanced tools (OCR, compression)',
                    'Priority processing',
                    'Email support',
                    '2 months free'
                ]
            },
            'enterprise': {
                'name': 'Enterprise',
                'price_id': os.getenv('STRIPE_ENTERPRISE_PRICE_ID'),
                'tier': 'enterprise',
                'features': [
                    'Everything in Pro',
                    'API access',
                    'White-label options',
                    'Custom integrations',
                    'Phone support'
                ]
            }
        }
    
    def create_customer(self, user_id: str, email: str, name: str = None) -> Optional[str]:
        """Create a Stripe customer for a user."""
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={'user_id': user_id}
            )
            
            # Update user with Stripe customer ID
            self.supabase.table('users').update({
                'stripe_customer_id': customer.id
            }).eq('id', user_id).execute()
            
            return customer.id
            
        except stripe.error.StripeError as e:
            print(f"Stripe error creating customer: {e}")
            return None
    
    def create_checkout_session(self, user_id: str, plan_key: str, success_url: str, cancel_url: str) -> Optional[str]:
        """Create a Stripe checkout session for subscription."""
        try:
            # Get user data
            user_response = self.supabase.table('users').select('*').eq('id', user_id).single().execute()
            if not user_response.data:
                return None
            
            user = user_response.data
            plan = self.plans.get(plan_key)
            
            if not plan or not plan['price_id']:
                return None
            
            # Create or get customer
            customer_id = user.get('stripe_customer_id')
            if not customer_id:
                customer_id = self.create_customer(user_id, user['email'], user.get('full_name'))
            
            if not customer_id:
                return None
            
            # Create checkout session
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': plan['price_id'],
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'user_id': user_id,
                    'plan_key': plan_key
                }
            )
            
            return session.url
            
        except stripe.error.StripeError as e:
            print(f"Stripe error creating checkout session: {e}")
            return None
    
    def create_portal_session(self, user_id: str, return_url: str) -> Optional[str]:
        """Create a Stripe customer portal session."""
        try:
            # Get user's Stripe customer ID
            user_response = self.supabase.table('users').select('stripe_customer_id').eq('id', user_id).single().execute()
            if not user_response.data or not user_response.data.get('stripe_customer_id'):
                return None
            
            # Create portal session
            session = stripe.billing_portal.Session.create(
                customer=user_response.data['stripe_customer_id'],
                return_url=return_url
            )
            
            return session.url
            
        except stripe.error.StripeError as e:
            print(f"Stripe error creating portal session: {e}")
            return None
    
    def handle_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """Handle Stripe webhook events."""
        try:
            # Verify webhook signature
            event = stripe.Webhook.construct_event(
                payload, signature, self.stripe_webhook_secret
            )
            
            event_type = event['type']
            data = event['data']['object']
            
            if event_type == 'checkout.session.completed':
                return self._handle_checkout_completed(data)
            
            elif event_type == 'customer.subscription.created':
                return self._handle_subscription_created(data)
            
            elif event_type == 'customer.subscription.updated':
                return self._handle_subscription_updated(data)
            
            elif event_type == 'customer.subscription.deleted':
                return self._handle_subscription_deleted(data)
            
            elif event_type == 'invoice.payment_succeeded':
                return self._handle_payment_succeeded(data)
            
            elif event_type == 'invoice.payment_failed':
                return self._handle_payment_failed(data)
            
            return {"success": True, "message": f"Unhandled event type: {event_type}"}
            
        except ValueError as e:
            return {"success": False, "error": f"Invalid payload: {e}"}
        except stripe.error.SignatureVerificationError as e:
            return {"success": False, "error": f"Invalid signature: {e}"}
        except Exception as e:
            return {"success": False, "error": f"Webhook error: {e}"}
    
    def _handle_checkout_completed(self, session) -> Dict[str, Any]:
        """Handle successful checkout completion."""
        try:
            user_id = session['metadata'].get('user_id')
            subscription_id = session.get('subscription')
            
            if user_id and subscription_id:
                # Get subscription details
                subscription = stripe.Subscription.retrieve(subscription_id)
                
                # Update user subscription status
                plan_tier = self._get_plan_tier_from_price_id(subscription['items']['data'][0]['price']['id'])
                
                self.supabase.table('users').update({
                    'subscription_tier': plan_tier,
                    'subscription_status': 'active',
                    'stripe_subscription_id': subscription_id
                }).eq('id', user_id).execute()
                
                # Create subscription record
                self._create_subscription_record(user_id, subscription)
            
            return {"success": True, "message": "Checkout completed"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _handle_subscription_created(self, subscription) -> Dict[str, Any]:
        """Handle subscription creation."""
        try:
            customer_id = subscription['customer']
            
            # Get user by customer ID
            user_response = self.supabase.table('users').select('id').eq('stripe_customer_id', customer_id).single().execute()
            if user_response.data:
                user_id = user_response.data['id']
                self._create_subscription_record(user_id, subscription)
            
            return {"success": True, "message": "Subscription created"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _handle_subscription_updated(self, subscription) -> Dict[str, Any]:
        """Handle subscription updates."""
        try:
            subscription_id = subscription['id']
            status = subscription['status']
            
            # Update subscription in database
            self.supabase.table('subscriptions').update({
                'status': status,
                'current_period_start': datetime.fromtimestamp(subscription['current_period_start']).isoformat(),
                'current_period_end': datetime.fromtimestamp(subscription['current_period_end']).isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }).eq('stripe_subscription_id', subscription_id).execute()
            
            # Update user status
            customer_id = subscription['customer']
            user_response = self.supabase.table('users').select('id').eq('stripe_customer_id', customer_id).single().execute()
            
            if user_response.data:
                plan_tier = self._get_plan_tier_from_price_id(subscription['items']['data'][0]['price']['id'])
                
                self.supabase.table('users').update({
                    'subscription_tier': plan_tier if status == 'active' else 'free',
                    'subscription_status': status
                }).eq('id', user_response.data['id']).execute()
            
            return {"success": True, "message": "Subscription updated"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _handle_subscription_deleted(self, subscription) -> Dict[str, Any]:
        """Handle subscription deletion."""
        try:
            subscription_id = subscription['id']
            customer_id = subscription['customer']
            
            # Update subscription status
            self.supabase.table('subscriptions').update({
                'status': 'cancelled',
                'cancelled_at': datetime.utcnow().isoformat()
            }).eq('stripe_subscription_id', subscription_id).execute()
            
            # Update user to free tier
            user_response = self.supabase.table('users').select('id').eq('stripe_customer_id', customer_id).single().execute()
            if user_response.data:
                self.supabase.table('users').update({
                    'subscription_tier': 'free',
                    'subscription_status': 'cancelled'
                }).eq('id', user_response.data['id']).execute()
            
            return {"success": True, "message": "Subscription cancelled"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _handle_payment_succeeded(self, invoice) -> Dict[str, Any]:
        """Handle successful payment."""
        # Log successful payment in audit log
        customer_id = invoice['customer']
        user_response = self.supabase.table('users').select('id').eq('stripe_customer_id', customer_id).single().execute()
        
        if user_response.data:
            self.supabase.table('audit_log').insert({
                'user_id': user_response.data['id'],
                'action': 'payment_succeeded',
                'resource_type': 'invoice',
                'resource_id': invoice['id'],
                'metadata': {
                    'amount': invoice['amount_paid'],
                    'currency': invoice['currency']
                }
            }).execute()
        
        return {"success": True, "message": "Payment succeeded"}
    
    def _handle_payment_failed(self, invoice) -> Dict[str, Any]:
        """Handle failed payment."""
        # Log failed payment and potentially update user status
        customer_id = invoice['customer']
        user_response = self.supabase.table('users').select('id').eq('stripe_customer_id', customer_id).single().execute()
        
        if user_response.data:
            self.supabase.table('audit_log').insert({
                'user_id': user_response.data['id'],
                'action': 'payment_failed',
                'resource_type': 'invoice',
                'resource_id': invoice['id'],
                'metadata': {
                    'amount': invoice['amount_due'],
                    'currency': invoice['currency']
                }
            }).execute()
            
            # Update user status if needed
            self.supabase.table('users').update({
                'subscription_status': 'past_due'
            }).eq('id', user_response.data['id']).execute()
        
        return {"success": True, "message": "Payment failed"}
    
    def _create_subscription_record(self, user_id: str, subscription) -> None:
        """Create subscription record in database."""
        subscription_data = {
            'user_id': user_id,
            'stripe_subscription_id': subscription['id'],
            'stripe_customer_id': subscription['customer'],
            'stripe_price_id': subscription['items']['data'][0]['price']['id'],
            'status': subscription['status'],
            'current_period_start': datetime.fromtimestamp(subscription['current_period_start']).isoformat(),
            'current_period_end': datetime.fromtimestamp(subscription['current_period_end']).isoformat(),
        }
        
        if subscription.get('trial_start'):
            subscription_data['trial_start'] = datetime.fromtimestamp(subscription['trial_start']).isoformat()
        
        if subscription.get('trial_end'):
            subscription_data['trial_end'] = datetime.fromtimestamp(subscription['trial_end']).isoformat()
        
        self.supabase.table('subscriptions').insert(subscription_data).execute()
    
    def _get_plan_tier_from_price_id(self, price_id: str) -> str:
        """Get plan tier from Stripe price ID."""
        for plan_key, plan_data in self.plans.items():
            if plan_data['price_id'] == price_id:
                return plan_data['tier']
        return 'free'
    
    def get_user_subscription(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's current subscription details."""
        try:
            subscription_response = self.supabase.table('subscriptions').select('*').eq(
                'user_id', user_id
            ).eq('status', 'active').single().execute()
            
            if subscription_response.data:
                return subscription_response.data
            
            return None
            
        except Exception:
            return None
    
    def cancel_subscription(self, user_id: str) -> Dict[str, Any]:
        """Cancel user's subscription at period end."""
        try:
            subscription = self.get_user_subscription(user_id)
            if not subscription:
                return {"success": False, "error": "No active subscription found"}
            
            # Cancel at period end in Stripe
            stripe.Subscription.modify(
                subscription['stripe_subscription_id'],
                cancel_at_period_end=True
            )
            
            # Update local record
            self.supabase.table('subscriptions').update({
                'cancel_at': subscription['current_period_end']
            }).eq('id', subscription['id']).execute()
            
            return {"success": True, "message": "Subscription will cancel at period end"}
            
        except stripe.error.StripeError as e:
            return {"success": False, "error": str(e)}

# Global payment manager instance
payment_manager = PaymentManager()