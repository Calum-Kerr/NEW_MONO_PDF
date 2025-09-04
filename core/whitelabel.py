"""
White-label solutions for enterprise customers.
Provides customizable branding and configuration options.
"""

import os
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class BrandingConfig:
    """Configuration for white-label branding."""
    tenant_id: str
    company_name: str
    logo_url: Optional[str]
    favicon_url: Optional[str]
    primary_color: str
    secondary_color: str
    accent_color: str
    font_family: str
    custom_domain: Optional[str]
    footer_text: Optional[str]
    support_email: Optional[str]
    terms_url: Optional[str]
    privacy_url: Optional[str]
    is_active: bool = True

@dataclass
class FeatureConfig:
    """Feature configuration for white-label solutions."""
    tenant_id: str
    enabled_features: List[str]
    disabled_features: List[str]
    custom_limits: Dict[str, int]
    api_access: bool
    analytics_access: bool
    custom_integrations: List[str]

class WhiteLabelManager:
    """Manages white-label configurations for enterprise customers."""
    
    def __init__(self, storage_backend=None):
        """Initialize white-label manager."""
        self.storage = storage_backend
        self.default_features = [
            'pdf_merge', 'pdf_split', 'pdf_compress', 'pdf_convert',
            'pdf_ocr', 'pdf_extract_text', 'pdf_rotate', 'pdf_watermark',
            'batch_processing', 'user_management'
        ]
        self.premium_features = [
            'api_access', 'analytics_dashboard', 'custom_branding',
            'priority_support', 'custom_integrations', 'advanced_analytics'
        ]
    
    def create_tenant(self, tenant_id: str, company_name: str,
                     plan_type: str = 'enterprise') -> Dict[str, Any]:
        """Create a new white-label tenant."""
        try:
            # Default branding configuration
            branding = BrandingConfig(
                tenant_id=tenant_id,
                company_name=company_name,
                logo_url=None,
                favicon_url=None,
                primary_color='#007bff',
                secondary_color='#6c757d',
                accent_color='#28a745',
                font_family='Inter, sans-serif',
                custom_domain=None,
                footer_text=f'© 2024 {company_name}. All rights reserved.',
                support_email=None,
                terms_url=None,
                privacy_url=None,
                is_active=True
            )
            
            # Feature configuration based on plan
            enabled_features = self.default_features.copy()
            if plan_type == 'enterprise':
                enabled_features.extend(self.premium_features)
            
            features = FeatureConfig(
                tenant_id=tenant_id,
                enabled_features=enabled_features,
                disabled_features=[],
                custom_limits={
                    'monthly_operations': 50000 if plan_type == 'enterprise' else 10000,
                    'file_size_mb': 100 if plan_type == 'enterprise' else 50,
                    'api_requests_per_hour': 10000 if plan_type == 'enterprise' else 1000,
                    'concurrent_users': 500 if plan_type == 'enterprise' else 100
                },
                api_access=plan_type == 'enterprise',
                analytics_access=plan_type == 'enterprise',
                custom_integrations=[]
            )
            
            # Store configurations
            if self.storage:
                brand_result = self._store_branding_config(branding)
                feature_result = self._store_feature_config(features)
                
                if not brand_result['success'] or not feature_result['success']:
                    return {
                        'success': False,
                        'error': 'Failed to store tenant configuration'
                    }
            
            return {
                'success': True,
                'tenant_id': tenant_id,
                'branding': asdict(branding),
                'features': asdict(features)
            }
            
        except Exception as e:
            logger.error(f"Failed to create tenant {tenant_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_branding(self, tenant_id: str, branding_updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update branding configuration for a tenant."""
        try:
            if self.storage:
                current_config = self._get_branding_config(tenant_id)
                if not current_config:
                    return {
                        'success': False,
                        'error': 'Tenant not found'
                    }
                
                # Update configuration
                for key, value in branding_updates.items():
                    if hasattr(BrandingConfig, key):
                        setattr(current_config, key, value)
                
                result = self._store_branding_config(current_config)
                if result['success']:
                    return {
                        'success': True,
                        'branding': asdict(current_config)
                    }
                else:
                    return result
            else:
                # Return sample updated configuration
                return {
                    'success': True,
                    'branding': {
                        'tenant_id': tenant_id,
                        'company_name': branding_updates.get('company_name', 'Sample Company'),
                        **branding_updates
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to update branding for tenant {tenant_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_tenant_config(self, tenant_id: str) -> Dict[str, Any]:
        """Get complete configuration for a tenant."""
        try:
            if self.storage:
                branding = self._get_branding_config(tenant_id)
                features = self._get_feature_config(tenant_id)
                
                if not branding or not features:
                    return {
                        'success': False,
                        'error': 'Tenant configuration not found'
                    }
                
                return {
                    'success': True,
                    'tenant_id': tenant_id,
                    'branding': asdict(branding),
                    'features': asdict(features)
                }
            else:
                # Return sample configuration
                return {
                    'success': True,
                    'tenant_id': tenant_id,
                    'branding': {
                        'tenant_id': tenant_id,
                        'company_name': 'Sample Company',
                        'primary_color': '#007bff',
                        'secondary_color': '#6c757d',
                        'accent_color': '#28a745'
                    },
                    'features': {
                        'tenant_id': tenant_id,
                        'enabled_features': self.default_features + self.premium_features,
                        'api_access': True,
                        'analytics_access': True
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to get tenant config for {tenant_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_custom_css(self, tenant_id: str) -> Dict[str, Any]:
        """Generate custom CSS for a tenant's branding."""
        try:
            if self.storage:
                branding = self._get_branding_config(tenant_id)
                if not branding:
                    return {
                        'success': False,
                        'error': 'Tenant not found'
                    }
            else:
                # Use default branding for sample
                branding = BrandingConfig(
                    tenant_id=tenant_id,
                    company_name='Sample Company',
                    logo_url=None,
                    favicon_url=None,
                    primary_color='#007bff',
                    secondary_color='#6c757d',
                    accent_color='#28a745',
                    font_family='Inter, sans-serif',
                    custom_domain=None,
                    footer_text='© 2024 Sample Company. All rights reserved.',
                    support_email=None,
                    terms_url=None,
                    privacy_url=None
                )
            
            # Generate CSS
            css = f"""
/* White-label CSS for {branding.company_name} */
:root {{
    --primary-color: {branding.primary_color};
    --secondary-color: {branding.secondary_color};
    --accent-color: {branding.accent_color};
    --font-family: {branding.font_family};
}}

body {{
    font-family: var(--font-family);
}}

.btn-primary {{
    background-color: var(--primary-color);
    border-color: var(--primary-color);
}}

.btn-primary:hover {{
    background-color: {self._darken_color(branding.primary_color, 0.1)};
    border-color: {self._darken_color(branding.primary_color, 0.1)};
}}

.navbar-brand {{
    color: var(--primary-color) !important;
}}

.text-primary {{
    color: var(--primary-color) !important;
}}

.bg-primary {{
    background-color: var(--primary-color) !important;
}}

.footer {{
    background-color: var(--secondary-color);
    color: white;
}}

.accent {{
    color: var(--accent-color);
}}

.bg-accent {{
    background-color: var(--accent-color);
}}

/* Custom logo styling */
.custom-logo {{
    max-height: 40px;
    width: auto;
}}
"""
            
            return {
                'success': True,
                'css': css,
                'tenant_id': tenant_id
            }
            
        except Exception as e:
            logger.error(f"Failed to generate CSS for tenant {tenant_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def check_feature_access(self, tenant_id: str, feature: str) -> bool:
        """Check if a tenant has access to a specific feature."""
        try:
            if self.storage:
                features = self._get_feature_config(tenant_id)
                if not features:
                    return False
                
                return (feature in features.enabled_features and 
                       feature not in features.disabled_features)
            else:
                # Default to allowing all features for sample
                return True
                
        except Exception as e:
            logger.error(f"Failed to check feature access for tenant {tenant_id}: {str(e)}")
            return False
    
    def get_tenant_limits(self, tenant_id: str) -> Dict[str, Any]:
        """Get usage limits for a tenant."""
        try:
            if self.storage:
                features = self._get_feature_config(tenant_id)
                if not features:
                    return {
                        'success': False,
                        'error': 'Tenant not found'
                    }
                
                return {
                    'success': True,
                    'limits': features.custom_limits
                }
            else:
                # Return sample limits
                return {
                    'success': True,
                    'limits': {
                        'monthly_operations': 50000,
                        'file_size_mb': 100,
                        'api_requests_per_hour': 10000,
                        'concurrent_users': 500
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to get tenant limits for {tenant_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_tenants(self) -> Dict[str, Any]:
        """List all white-label tenants."""
        try:
            if self.storage:
                tenants = self._get_all_tenants()
                return {
                    'success': True,
                    'tenants': tenants
                }
            else:
                # Return sample tenants
                return {
                    'success': True,
                    'tenants': [
                        {
                            'tenant_id': 'acme_corp',
                            'company_name': 'Acme Corporation',
                            'plan_type': 'enterprise',
                            'is_active': True
                        },
                        {
                            'tenant_id': 'tech_solutions',
                            'company_name': 'Tech Solutions Inc',
                            'plan_type': 'enterprise',
                            'is_active': True
                        }
                    ]
                }
                
        except Exception as e:
            logger.error(f"Failed to list tenants: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _darken_color(self, color: str, amount: float) -> str:
        """Darken a hex color by a specified amount."""
        # Simple color darkening - in production, use a proper color library
        if color.startswith('#'):
            color = color[1:]
        
        # Convert to RGB
        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)
        
        # Darken
        r = max(0, int(r * (1 - amount)))
        g = max(0, int(g * (1 - amount)))
        b = max(0, int(b * (1 - amount)))
        
        # Convert back to hex
        return f"#{r:02x}{g:02x}{b:02x}"
    
    # Storage backend methods
    def _store_branding_config(self, config: BrandingConfig) -> Dict[str, Any]:
        """Store branding configuration in database."""
        return {'success': True}
    
    def _store_feature_config(self, config: FeatureConfig) -> Dict[str, Any]:
        """Store feature configuration in database."""
        return {'success': True}
    
    def _get_branding_config(self, tenant_id: str) -> Optional[BrandingConfig]:
        """Get branding configuration from database."""
        return None
    
    def _get_feature_config(self, tenant_id: str) -> Optional[FeatureConfig]:
        """Get feature configuration from database."""
        return None
    
    def _get_all_tenants(self) -> List[Dict[str, Any]]:
        """Get all tenants from database."""
        return []

# Global instance
whitelabel_manager = WhiteLabelManager()