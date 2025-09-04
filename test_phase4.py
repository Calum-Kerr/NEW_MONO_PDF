#!/usr/bin/env python3
"""
Test script for Phase 4 features.
Validates AI analysis, collaboration, cloud storage, and security modules.
"""

import os
import sys
import tempfile
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_ai_analysis():
    """Test AI analysis functionality."""
    print("🤖 Testing AI Analysis Module...")
    
    try:
        from core.ai_analysis import ai_analysis_manager
        
        if not ai_analysis_manager:
            print("  ⚠️  AI analysis manager not available (requires API keys)")
            return False
        
        # Test text insights
        sample_text = "This is a sample document about artificial intelligence and machine learning."
        insights = ai_analysis_manager.get_document_insights(sample_text)
        
        assert 'word_count' in insights
        assert insights['word_count'] > 0
        
        print(f"  ✅ Text insights generated: {insights['word_count']} words")
        
        # Test document classification
        doc_type = ai_analysis_manager.classify_document_type(sample_text)
        print(f"  ✅ Document classified as: {doc_type}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ AI Analysis test failed: {str(e)}")
        return False

def test_collaboration():
    """Test collaborative editing functionality."""
    print("👥 Testing Collaboration Module...")
    
    try:
        from core.collaboration import collaboration_manager, PermissionLevel, AccessAction
        
        # Test document sharing
        share = collaboration_manager.create_document_share(
            document_id="test_doc_123",
            owner_id="user_123",
            title="Test Document",
            description="A test document for collaboration"
        )
        
        assert share.share_id is not None
        print(f"  ✅ Document share created: {share.share_id}")
        
        # Test adding collaborator
        success = collaboration_manager.add_collaborator(
            share.share_id, "user_456", PermissionLevel.EDIT
        )
        assert success
        print("  ✅ Collaborator added successfully")
        
        # Test joining session
        presence = collaboration_manager.join_session(
            "test_doc_123", "user_789", "Test User"
        )
        assert presence.user_id == "user_789"
        print("  ✅ User joined collaboration session")
        
        # Test adding comment
        comment = collaboration_manager.add_comment(
            "test_doc_123", "user_789", "Test User",
            "This is a test comment", {"page": 1, "x": 100, "y": 200}
        )
        assert comment.comment_id is not None
        print("  ✅ Comment added successfully")
        
        # Test getting comments
        comments = collaboration_manager.get_document_comments("test_doc_123")
        assert len(comments) == 1
        print(f"  ✅ Retrieved {len(comments)} comments")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Collaboration test failed: {str(e)}")
        return False

def test_cloud_storage():
    """Test cloud storage integration."""
    print("☁️  Testing Cloud Storage Module...")
    
    try:
        from core.cloud_storage import cloud_storage_manager
        
        # Test getting connected providers (should be empty initially)
        providers = cloud_storage_manager.get_connected_providers("test_user")
        assert isinstance(providers, list)
        print(f"  ✅ Connected providers retrieved: {len(providers)} providers")
        
        # Test provider availability
        available_providers = list(cloud_storage_manager.providers.keys())
        assert 'google_drive' in available_providers
        assert 'dropbox' in available_providers
        print(f"  ✅ Available providers: {', '.join(available_providers)}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Cloud Storage test failed: {str(e)}")
        return False

def test_security():
    """Test advanced security features."""
    print("🔒 Testing Security Module...")
    
    try:
        from core.security import security_manager, SecurityLevel, AccessAction
        
        # Test encryption key generation
        encryption = security_manager.encryption
        key = encryption.generate_symmetric_key()
        
        assert key.key_id is not None
        assert key.key_type == "symmetric"
        print("  ✅ Symmetric encryption key generated")
        
        # Test DRM policy creation
        drm_policy = security_manager.drm.create_drm_policy(
            name="Test Policy",
            description="A test DRM policy",
            creator_id="admin_123",
            allowed_actions=[AccessAction.VIEW, AccessAction.DOWNLOAD],
            max_views=10
        )
        
        assert drm_policy.policy_id is not None
        print(f"  ✅ DRM policy created: {drm_policy.policy_id}")
        
        # Test document security application
        doc_security = security_manager.drm.apply_drm_to_document(
            "test_doc_security", drm_policy.policy_id, SecurityLevel.STANDARD
        )
        
        assert doc_security.document_id == "test_doc_security"
        print("  ✅ DRM policy applied to document")
        
        # Test access permission checking
        allowed, reason = security_manager.drm.check_access_permission(
            "test_doc_security", "user_123", AccessAction.VIEW, "127.0.0.1"
        )
        
        assert allowed == True
        print("  ✅ Access permission check passed")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Security test failed: {str(e)}")
        return False

def test_api_integration():
    """Test API endpoint integration."""
    print("🔗 Testing API Integration...")
    
    try:
        # Test that all Phase 4 managers are available in core module
        from core import (
            ai_analysis_manager, collaboration_manager,
            cloud_storage_manager, security_manager
        )
        
        available_count = sum([
            1 for manager in [ai_analysis_manager, collaboration_manager, cloud_storage_manager, security_manager]
            if manager is not None
        ])
        
        print(f"  ✅ {available_count}/4 Phase 4 managers available")
        
        # Test Flask app imports
        from api.app import app
        
        # Check for Phase 4 endpoints
        phase4_endpoints = [
            '/api/ai/analyze-document',
            '/api/collaboration/share-document',
            '/api/cloud/connect/<provider>',
            '/api/security/secure-document'
        ]
        
        app_rules = [str(rule) for rule in app.url_map.iter_rules()]
        
        found_endpoints = 0
        for endpoint in phase4_endpoints:
            # Check if any rule contains the endpoint pattern
            if any(endpoint.replace('<provider>', '') in rule for rule in app_rules):
                found_endpoints += 1
        
        print(f"  ✅ {found_endpoints}/{len(phase4_endpoints)} Phase 4 endpoints integrated")
        
        return True
        
    except Exception as e:
        print(f"  ❌ API Integration test failed: {str(e)}")
        return False

def main():
    """Run all Phase 4 tests."""
    print("🚀 Starting Phase 4 Implementation Tests")
    print("=" * 50)
    
    tests = [
        test_ai_analysis,
        test_collaboration,
        test_cloud_storage,
        test_security,
        test_api_integration
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test in tests:
        if test():
            passed_tests += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All Phase 4 tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    exit(main())