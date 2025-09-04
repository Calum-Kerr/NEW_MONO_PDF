import stripe
import os
from supabase import create_client, Client
from datetime import datetime, timedelta

class StripeManager:
    def __init__(self):
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        self.webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)

    def create_checkout_session(self, user_id: str, user_email: str, price_id: str, 
                              success_url: str = None, cancel_url: str = None):
        """Create Stripe checkout session for subscription"""
        try:
            # Default URLs if not provided
            if not success_url:
                success_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/success?session_id={{CHECKOUT_SESSION_ID}}"
            if not cancel_url:
                cancel_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/pricing"

            # Get or create Stripe customer
            customer_result = self.get_or_create_customer(user_id, user_email)
            if not customer_result['success']:
                return customer_result

            customer_id = customer_result['customer_id']

            # Create checkout session
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'user_id': user_id
                }
            )

            return {
                'success': True,
                'checkout_url': session.url,
                'session_id': session.id
            }

        except stripe.error.StripeError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_or_create_customer(self, user_id: str, email: str):
        """Get existing Stripe customer or create new one"""
        try:
            # Check if customer already exists in our database
            customer_result = self.supabase.table('subscriptions').select(
                'stripe_customer_id'
            ).eq('user_id', user_id).execute()

            if customer_result.data and customer_result.data[0]['stripe_customer_id']:
                return {
                    'success': True,
                    'customer_id': customer_result.data[0]['stripe_customer_id']
                }

            # Create new Stripe customer
            customer = stripe.Customer.create(
                email=email,
                metadata={'user_id': user_id}
            )

            return {
                'success': True,
                'customer_id': customer.id
            }

        except stripe.error.StripeError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def handle_webhook(self, payload: bytes, sig_header: str):
        """Handle Stripe webhook events"""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )

            # Handle different event types
            if event['type'] == 'checkout.session.completed':
                self.handle_checkout_completed(event['data']['object'])
            elif event['type'] == 'customer.subscription.created':
                self.handle_subscription_created(event['data']['object'])
            elif event['type'] == 'customer.subscription.updated':
                self.handle_subscription_updated(event['data']['object'])
            elif event['type'] == 'customer.subscription.deleted':
                self.handle_subscription_deleted(event['data']['object'])
            elif event['type'] == 'invoice.payment_succeeded':
                self.handle_payment_succeeded(event['data']['object'])
            elif event['type'] == 'invoice.payment_failed':
                self.handle_payment_failed(event['data']['object'])

            return {'success': True}

        except stripe.error.SignatureVerificationError as e:
            return {'success': False, 'error': 'Invalid signature'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def handle_checkout_completed(self, session):
        """Handle successful checkout completion"""
        try:
            user_id = session['metadata']['user_id']
            customer_id = session['customer']
            subscription_id = session['subscription']

            # Get subscription details from Stripe
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            # Update user subscription status
            self.supabase.table('users').update({
                'subscription_status': 'premium'
            }).eq('id', user_id).execute()

            # Create or update subscription record
            subscription_data = {
                'user_id': user_id,
                'stripe_subscription_id': subscription_id,
                'stripe_customer_id': customer_id,
                'status': subscription['status'],
                'plan_name': 'premium',
                'plan_price': subscription['items']['data'][0]['price']['unit_amount'] / 100,
                'currency': subscription['items']['data'][0]['price']['currency'].upper(),
                'current_period_start': datetime.fromtimestamp(
                    subscription['current_period_start']
                ).isoformat(),
                'current_period_end': datetime.fromtimestamp(
                    subscription['current_period_end']
                ).isoformat()
            }

            # Upsert subscription
            self.supabase.table('subscriptions').upsert(
                subscription_data, on_conflict='user_id'
            ).execute()

            # Update usage limits for premium user
            self.update_usage_limits(user_id, 'premium')

        except Exception as e:
            print(f"Error handling checkout completion: {str(e)}")

    def handle_subscription_created(self, subscription):
        """Handle subscription creation"""
        # This is typically handled in checkout.session.completed
        pass

    def handle_subscription_updated(self, subscription):
        """Handle subscription updates"""
        try:
            # Find user by customer ID
            customer_result = self.supabase.table('subscriptions').select(
                'user_id'
            ).eq('stripe_customer_id', subscription['customer']).execute()

            if not customer_result.data:
                return

            user_id = customer_result.data[0]['user_id']

            # Update subscription record
            update_data = {
                'status': subscription['status'],
                'current_period_start': datetime.fromtimestamp(
                    subscription['current_period_start']
                ).isoformat(),
                'current_period_end': datetime.fromtimestamp(
                    subscription['current_period_end']
                ).isoformat(),
                'cancel_at_period_end': subscription['cancel_at_period_end']
            }

            self.supabase.table('subscriptions').update(update_data).eq(
                'stripe_subscription_id', subscription['id']
            ).execute()

            # Update user status based on subscription status
            user_status = 'premium' if subscription['status'] == 'active' else 'free'
            self.supabase.table('users').update({
                'subscription_status': user_status
            }).eq('id', user_id).execute()

        except Exception as e:
            print(f"Error handling subscription update: {str(e)}")

    def handle_subscription_deleted(self, subscription):
        """Handle subscription cancellation"""
        try:
            # Find user by customer ID
            customer_result = self.supabase.table('subscriptions').select(
                'user_id'
            ).eq('stripe_customer_id', subscription['customer']).execute()

            if not customer_result.data:
                return

            user_id = customer_result.data[0]['user_id']

            # Update subscription status
            self.supabase.table('subscriptions').update({
                'status': 'canceled'
            }).eq('stripe_subscription_id', subscription['id']).execute()

            # Update user status
            self.supabase.table('users').update({
                'subscription_status': 'free'
            }).eq('id', user_id).execute()

            # Update usage limits back to free tier
            self.update_usage_limits(user_id, 'free')

        except Exception as e:
            print(f"Error handling subscription deletion: {str(e)}")

    def handle_payment_succeeded(self, invoice):
        """Handle successful payment"""
        # Log successful payment for analytics
        pass

    def handle_payment_failed(self, invoice):
        """Handle failed payment"""
        # Handle failed payment (send notification, update status, etc.)
        pass

    def cancel_subscription(self, user_id: str):
        """Cancel user's subscription"""
        try:
            # Get subscription
            subscription_result = self.supabase.table('subscriptions').select(
                'stripe_subscription_id'
            ).eq('user_id', user_id).execute()

            if not subscription_result.data:
                return {'success': False, 'error': 'No active subscription found'}

            stripe_subscription_id = subscription_result.data[0]['stripe_subscription_id']

            # Cancel at period end in Stripe
            stripe.Subscription.modify(
                stripe_subscription_id,
                cancel_at_period_end=True
            )

            # Update local record
            self.supabase.table('subscriptions').update({
                'cancel_at_period_end': True
            }).eq('user_id', user_id).execute()

            return {'success': True}

        except stripe.error.StripeError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_subscription_status(self, user_id: str):
        """Get user's subscription status and usage"""
        try:
            # Get subscription and usage data
            subscription_result = self.supabase.table('user_current_usage').select(
                '*'
            ).eq('user_id', user_id).execute()

            if subscription_result.data:
                data = subscription_result.data[0]
                return {
                    'success': True,
                    'subscription': {
                        'status': data['subscription_status'],
                        'period_end': data.get('period_end'),
                        'cancel_at_period_end': False  # Would need to join with subscriptions table
                    },
                    'usage': {
                        'jobs_used': data['jobs_used'],
                        'jobs_limit': data['jobs_limit'],
                        'file_size_used': data['file_size_used'],
                        'file_size_limit': data['file_size_limit'],
                        'period_start': data['period_start'],
                        'period_end': data['period_end']
                    }
                }
            else:
                return {'success': False, 'error': 'User not found'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_usage_stats(self, user_id: str):
        """Get detailed usage statistics"""
        try:
            usage_result = self.supabase.table('user_current_usage').select(
                '*'
            ).eq('user_id', user_id).execute()

            if usage_result.data:
                usage = usage_result.data[0]
                return {
                    'success': True,
                    'usage': {
                        'jobs_used': usage['jobs_used'],
                        'jobs_limit': usage['jobs_limit'],
                        'jobs_remaining': usage['jobs_limit'] - usage['jobs_used'],
                        'file_size_used': usage['file_size_used'],
                        'file_size_limit': usage['file_size_limit'],
                        'file_size_remaining': usage['file_size_limit'] - usage['file_size_used'],
                        'period_start': usage['period_start'],
                        'period_end': usage['period_end'],
                        'subscription_status': usage['subscription_status']
                    }
                }
            else:
                return {'success': False, 'error': 'Usage data not found'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def update_usage_limits(self, user_id: str, plan: str):
        """Update usage limits based on subscription plan"""
        try:
            # Define limits for different plans
            limits = {
                'free': {
                    'jobs_limit': 5,
                    'file_size_limit': 10485760  # 10MB
                },
                'premium': {
                    'jobs_limit': 100,
                    'file_size_limit': 104857600  # 100MB
                },
                'enterprise': {
                    'jobs_limit': 1000,
                    'file_size_limit': 1073741824  # 1GB
                }
            }

            plan_limits = limits.get(plan, limits['free'])

            # Update current usage limits
            self.supabase.table('usage_limits').update(plan_limits).eq(
                'user_id', user_id
            ).eq(
                'period_start', '<=', datetime.utcnow().isoformat()
            ).eq(
                'period_end', '>=', datetime.utcnow().isoformat()
            ).execute()

        except Exception as e:
            print(f"Error updating usage limits: {str(e)}")

    def check_usage_limits(self, user_id: str, job_type: str = None, file_size: int = 0):
        """Check if user can perform action based on usage limits"""
        try:
            usage_result = self.supabase.table('user_current_usage').select(
                '*'
            ).eq('user_id', user_id).execute()

            if not usage_result.data:
                return {'success': False, 'error': 'User usage data not found'}

            usage = usage_result.data[0]

            # Check job limit
            if usage['jobs_used'] >= usage['jobs_limit']:
                return {
                    'success': False, 
                    'error': 'Job limit exceeded. Please upgrade your plan.',
                    'limit_type': 'jobs'
                }

            # Check file size limit
            if usage['file_size_used'] + file_size > usage['file_size_limit']:
                return {
                    'success': False,
                    'error': 'File size limit exceeded. Please upgrade your plan.',
                    'limit_type': 'file_size'
                }

            return {'success': True}

        except Exception as e:
            return {'success': False, 'error': str(e)}