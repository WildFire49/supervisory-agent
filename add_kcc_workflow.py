#!/usr/bin/env python3
"""
Script to add the Federal Bank KCC (Kisan Credit Card) workflow schema to the database.
This will insert the workflow for bank_name="federal" and product_type="kcc".
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal, Workflow
import json

def add_kcc_workflow():
    """Add the KCC workflow schema to the database"""
    
    # KCC Action Schema - converted from the JavaScript file
    kcc_action_schema = [
        {
            "id": "kcc-welcome",
            "stage_name": "KCC Welcome Screen",
            "action_type": "WELCOME_SCREEN",
            "next_success_action_id": "verify-otp",
            "ui_id": "ui_kcc_welcome_001",
            "priority": 1,
            "is_mandatory": True,
            "flow_type": "kcc",
            "desc_for_llm": "Initial welcome screen for KCC application process"
        },
        {
            "id": "verify-otp",
            "stage_name": "Verify OTP",
            "action_type": "OTP_VERIFICATION",
            "next_success_action_id": "aadhar-verification",
            "ui_id": "ui_verify_otp_001",
            "priority": 2,
            "is_mandatory": True,
            "flow_type": "kcc",
            "desc_for_llm": "OTP verification for mobile number validation"
        },
        {
            "id": "aadhar-verification",
            "stage_name": "Add Aadhar Number",
            "action_type": "AADHAR_VERIFICATION",
            "next_success_action_id": "applicant-details",
            "ui_id": "ui_aadhar_verification_001",
            "priority": 3,
            "is_mandatory": True,
            "flow_type": "kcc",
            "desc_for_llm": "Aadhar number verification with fingerprint scanning"
        },
        {
            "id": "applicant-details",
            "stage_name": "Capture Applicant Details",
            "action_type": "APPLICANT_DETAILS",
            "next_success_action_id": "customer-photo",
            "ui_id": "ui_applicant_details_001",
            "priority": 4,
            "is_mandatory": True,
            "flow_type": "kcc",
            "desc_for_llm": "Capture personal details like name, DOB, gender, parents' names"
        },
        {
            "id": "customer-photo",
            "stage_name": "Capture Customer Photo",
            "action_type": "PHOTO_CAPTURE",
            "next_success_action_id": "residence-details",
            "ui_id": "ui_customer_photo_001",
            "priority": 5,
            "is_mandatory": True,
            "flow_type": "kcc",
            "desc_for_llm": "Capture customer photograph for identification"
        },
        {
            "id": "residence-details",
            "stage_name": "Capture Residence Details",
            "action_type": "RESIDENCE_DETAILS",
            "next_success_action_id": "bank-master",
            "ui_id": "ui_residence_details_001",
            "priority": 6,
            "is_mandatory": True,
            "flow_type": "kcc",
            "desc_for_llm": "Capture KYC address including house number, street, locality, VTC"
        },
        {
            "id": "bank-master",
            "stage_name": "Capture Bank Master",
            "action_type": "BANK_MASTER",
            "next_success_action_id": "pan-details",
            "ui_id": "ui_bank_master_001",
            "priority": 7,
            "is_mandatory": True,
            "flow_type": "kcc",
            "desc_for_llm": "Capture bank location details including country, state, city, district"
        },
        {
            "id": "pan-details",
            "stage_name": "Capture PAN Card Details",
            "action_type": "PAN_DETAILS",
            "next_success_action_id": "secondary-kyc",
            "ui_id": "ui_pan_details_001",
            "priority": 8,
            "is_mandatory": False,
            "flow_type": "kcc",
            "desc_for_llm": "Optional PAN card details capture with document upload"
        },
        {
            "id": "secondary-kyc",
            "stage_name": "Capture Secondary KYC",
            "action_type": "SECONDARY_KYC",
            "next_success_action_id": "demographics-success",
            "ui_id": "ui_secondary_kyc_001",
            "priority": 9,
            "is_mandatory": True,
            "flow_type": "kcc",
            "desc_for_llm": "Secondary KYC document capture (Passport, Voter ID, Driver's License)"
        },
        {
            "id": "demographics-success",
            "stage_name": "Demographics Success",
            "action_type": "SUCCESS_MESSAGE",
            "next_success_action_id": "kcc-details",
            "ui_id": "ui_demographics_success_001",
            "priority": 10,
            "is_mandatory": True,
            "flow_type": "kcc",
            "desc_for_llm": "Success message after demographics completion"
        },
        {
            "id": "kcc-details",
            "stage_name": "Capture KCC Details",
            "action_type": "KCC_DETAILS",
            "next_success_action_id": "land-details",
            "ui_id": "ui_kcc_details_001",
            "priority": 11,
            "is_mandatory": True,
            "flow_type": "kcc",
            "desc_for_llm": "Capture KCC specific details and customer list"
        },
        {
            "id": "land-details",
            "stage_name": "Capture Land Details",
            "action_type": "LAND_DETAILS",
            "next_success_action_id": None,  # Final step
            "ui_id": "ui_land_details_001",
            "priority": 12,
            "is_mandatory": True,
            "flow_type": "kcc",
            "desc_for_llm": "Final step - capture agricultural land details including state, district, village, survey number"
        }
    ]
    
    # KCC UI Schema - key UI components for each step
    kcc_ui_schema = {
        "kcc-welcome": {
            "id": "ui_kcc_welcome_001",
            "screen_id": "kcc_welcome_screen",
            "ui_components": [
                {
                    "id": "kcc_welcome_container",
                    "component_type": "Container",
                    "properties": {"padding": "24px", "textAlign": "center"},
                    "children": [
                        {
                            "id": "kcc_welcome_title",
                            "component_type": "Text",
                            "properties": {
                                "text": "Welcome to Kisan Credit Card Application",
                                "variant": "h6",
                                "color": "primary",
                                "sx": {"fontWeight": "bold", "mb": 2}
                            }
                        },
                        {
                            "id": "kcc_welcome_subtitle",
                            "component_type": "Text",
                            "properties": {
                                "text": "Apply for agricultural loans with ease",
                                "variant": "body1",
                                "color": "text.secondary",
                                "sx": {"mb": 4}
                            }
                        },
                        {
                            "id": "kcc_start_button",
                            "component_type": "Button",
                            "properties": {
                                "text": "Start Application",
                                "variant": "contained",
                                "color": "primary",
                                "size": "large",
                                "action": {
                                    "type": "navigate_to",
                                    "action_id": "kcc-welcome",
                                    "next_success_action_id": "verify-otp"
                                }
                            }
                        }
                    ]
                }
            ]
        },
        "verify-otp": {
            "id": "ui_verify_otp_001",
            "screen_id": "verify_otp_screen",
            "ui_components": [
                {
                    "id": "otp_container",
                    "component_type": "Container",
                    "properties": {"padding": "24px"},
                    "children": [
                        {
                            "id": "otp_title",
                            "component_type": "Text",
                            "properties": {
                                "text": "Verify OTP",
                                "variant": "h6",
                                "color": "primary",
                                "sx": {"fontWeight": "bold", "mb": 2, "textAlign": "center"}
                            }
                        },
                        {
                            "id": "otp_input",
                            "component_type": "OTPInput",
                            "properties": {
                                "label": "Enter 4-digit OTP",
                                "length": 4,
                                "required": True,
                                "sx": {"mb": 3}
                            }
                        },
                        {
                            "id": "verify_otp_button",
                            "component_type": "Button",
                            "properties": {
                                "text": "Verify",
                                "variant": "contained",
                                "color": "primary",
                                "fullWidth": True,
                                "action": {
                                    "type": "submit_form",
                                    "action_id": "verify-otp",
                                    "next_success_action_id": "aadhar-verification"
                                }
                            }
                        }
                    ]
                }
            ]
        },
        "aadhar-verification": {
            "id": "ui_aadhar_verification_001",
            "screen_id": "aadhar_verification_screen",
            "ui_components": [
                {
                    "id": "aadhar_container",
                    "component_type": "Container",
                    "properties": {"padding": "24px"},
                    "children": [
                        {
                            "id": "aadhar_title",
                            "component_type": "Text",
                            "properties": {
                                "text": "Add your Aadhar Number",
                                "variant": "h6",
                                "color": "primary",
                                "sx": {"fontWeight": "bold", "mb": 3}
                            }
                        },
                        {
                            "id": "aadhar_input",
                            "component_type": "Input",
                            "properties": {
                                "label": "Enter your 12 digit Aadhar Number",
                                "placeholder": "XXXX XXXX XXXX",
                                "type": "text",
                                "maxLength": 12,
                                "required": True,
                                "sx": {"mb": 3}
                            }
                        },
                        {
                            "id": "fingerprint_scanner",
                            "component_type": "FingerprintScanner",
                            "properties": {
                                "label": "Tap to scan with fingerprint",
                                "sx": {"mb": 3}
                            }
                        },
                        {
                            "id": "verify_aadhar_button",
                            "component_type": "Button",
                            "properties": {
                                "text": "Verify",
                                "variant": "contained",
                                "color": "primary",
                                "fullWidth": True,
                                "action": {
                                    "type": "submit_form",
                                    "action_id": "aadhar-verification",
                                    "next_success_action_id": "applicant-details"
                                }
                            }
                        }
                    ]
                }
            ]
        },
        "applicant-details": {
            "id": "ui_applicant_details_001",
            "screen_id": "applicant_details_screen",
            "ui_components": [
                {
                    "id": "applicant_container",
                    "component_type": "Container",
                    "properties": {"padding": "24px"},
                    "children": [
                        {
                            "id": "applicant_title",
                            "component_type": "Text",
                            "properties": {
                                "text": "Capture Applicant Details",
                                "variant": "h6",
                                "color": "primary",
                                "sx": {"fontWeight": "bold", "mb": 3}
                            }
                        },
                        {
                            "id": "full_name_input",
                            "component_type": "Input",
                            "properties": {
                                "label": "Full Name",
                                "placeholder": "Enter your full name",
                                "required": True,
                                "sx": {"mb": 2}
                            }
                        },
                        {
                            "id": "dob_input",
                            "component_type": "DatePicker",
                            "properties": {
                                "label": "Date of Birth",
                                "required": True,
                                "sx": {"mb": 2}
                            }
                        },
                        {
                            "id": "gender_selector",
                            "component_type": "Selector",
                            "properties": {
                                "label": "Gender",
                                "options": ["Male", "Female", "Others"],
                                "required": True,
                                "sx": {"mb": 2}
                            }
                        },
                        {
                            "id": "submit_applicant_button",
                            "component_type": "Button",
                            "properties": {
                                "text": "Continue",
                                "variant": "contained",
                                "color": "primary",
                                "fullWidth": True,
                                "action": {
                                    "type": "submit_form",
                                    "action_id": "applicant-details",
                                    "next_success_action_id": "customer-photo"
                                }
                            }
                        }
                    ]
                }
            ]
        },
        "customer-photo": {
            "id": "ui_customer_photo_001",
            "screen_id": "customer_photo_screen",
            "ui_components": [
                {
                    "id": "photo_container",
                    "component_type": "Container",
                    "properties": {"padding": "24px", "textAlign": "center"},
                    "children": [
                        {
                            "id": "photo_title",
                            "component_type": "Text",
                            "properties": {
                                "text": "Capture Customer Photo",
                                "variant": "h6",
                                "color": "primary",
                                "sx": {"fontWeight": "bold", "mb": 3}
                            }
                        },
                        {
                            "id": "customer_photo_capture",
                            "component_type": "ImageCapture",
                            "properties": {
                                "label": "Take Photo",
                                "required": True,
                                "sx": {"mb": 3}
                            }
                        },
                        {
                            "id": "continue_photo_button",
                            "component_type": "Button",
                            "properties": {
                                "text": "Continue",
                                "variant": "contained",
                                "color": "primary",
                                "fullWidth": True,
                                "action": {
                                    "type": "submit_form",
                                    "action_id": "customer-photo",
                                    "next_success_action_id": "residence-details"
                                }
                            }
                        }
                    ]
                }
            ]
        },
        "residence-details": {
            "id": "ui_residence_details_001",
            "screen_id": "residence_details_screen",
            "ui_components": [
                {
                    "id": "residence_container",
                    "component_type": "Container",
                    "properties": {"padding": "24px"},
                    "children": [
                        {
                            "id": "residence_title",
                            "component_type": "Text",
                            "properties": {
                                "text": "Capture Residence Details",
                                "variant": "h6",
                                "color": "primary",
                                "sx": {"fontWeight": "bold", "mb": 2}
                            }
                        },
                        {
                            "id": "house_number_input",
                            "component_type": "Input",
                            "properties": {
                                "label": "House Number",
                                "placeholder": "Enter house number",
                                "required": True,
                                "sx": {"mb": 2}
                            }
                        },
                        {
                            "id": "street_input",
                            "component_type": "Input",
                            "properties": {
                                "label": "Street",
                                "placeholder": "Enter street name",
                                "required": True,
                                "sx": {"mb": 2}
                            }
                        }
                    ]
                }
            ]
        },
        "bank-master": {
            "id": "ui_bank_master_001",
            "screen_id": "bank_master_screen",
            "ui_components": [
                {
                    "id": "bank_container",
                    "component_type": "Container",
                    "properties": {"padding": "24px"},
                    "children": [
                        {
                            "id": "bank_title",
                            "component_type": "Text",
                            "properties": {
                                "text": "Capture Bank Master",
                                "variant": "h6",
                                "color": "primary",
                                "sx": {"fontWeight": "bold", "mb": 3}
                            }
                        },
                        {
                            "id": "country_selector",
                            "component_type": "Selector",
                            "properties": {
                                "label": "Country",
                                "options": ["India", "USA", "UK", "Canada", "Australia"],
                                "defaultValue": "India",
                                "required": True,
                                "sx": {"mb": 2}
                            }
                        }
                    ]
                }
            ]
        },
        "pan-details": {
            "id": "ui_pan_details_001",
            "screen_id": "pan_details_screen",
            "ui_components": [
                {
                    "id": "pan_container",
                    "component_type": "Container",
                    "properties": {"padding": "24px"},
                    "children": [
                        {
                            "id": "pan_title",
                            "component_type": "Text",
                            "properties": {
                                "text": "Capture PAN Card Details",
                                "variant": "h6",
                                "color": "primary",
                                "sx": {"fontWeight": "bold", "mb": 3}
                            }
                        },
                        {
                            "id": "pan_available_checkbox",
                            "component_type": "Checkbox",
                            "properties": {
                                "label": "Is PAN Available?",
                                "required": True,
                                "sx": {"mb": 2}
                            }
                        }
                    ]
                }
            ]
        },
        "secondary-kyc": {
            "id": "ui_secondary_kyc_001",
            "screen_id": "secondary_kyc_screen",
            "ui_components": [
                {
                    "id": "secondary_kyc_container",
                    "component_type": "Container",
                    "properties": {"padding": "24px"},
                    "children": [
                        {
                            "id": "secondary_kyc_title",
                            "component_type": "Text",
                            "properties": {
                                "text": "Capture Secondary KYC",
                                "variant": "h6",
                                "color": "primary",
                                "sx": {"fontWeight": "bold", "mb": 2}
                            }
                        },
                        {
                            "id": "kyc_type_selector",
                            "component_type": "Selector",
                            "properties": {
                                "label": "Type",
                                "options": ["Passport", "Voter ID", "Driver's License"],
                                "required": True,
                                "sx": {"mb": 2}
                            }
                        }
                    ]
                }
            ]
        },
        "demographics-success": {
            "id": "ui_demographics_success_001",
            "screen_id": "demographics_success_screen",
            "ui_components": [
                {
                    "id": "success_container",
                    "component_type": "Container",
                    "properties": {"padding": "24px", "textAlign": "center"},
                    "children": [
                        {
                            "id": "success_title",
                            "component_type": "Text",
                            "properties": {
                                "text": "Demographics Details Submitted Successfully!",
                                "variant": "h6",
                                "color": "success.main",
                                "sx": {"fontWeight": "bold", "mb": 3}
                            }
                        },
                        {
                            "id": "continue_success_button",
                            "component_type": "Button",
                            "properties": {
                                "text": "Continue to KCC Details",
                                "variant": "contained",
                                "color": "primary",
                                "size": "large",
                                "action": {
                                    "type": "navigate_to",
                                    "action_id": "demographics-success",
                                    "next_success_action_id": "kcc-details"
                                }
                            }
                        }
                    ]
                }
            ]
        },
        "kcc-details": {
            "id": "ui_kcc_details_001",
            "screen_id": "kcc_details_screen",
            "ui_components": [
                {
                    "id": "kcc_details_container",
                    "component_type": "Container",
                    "properties": {"padding": "24px"},
                    "children": [
                        {
                            "id": "kcc_details_title",
                            "component_type": "Text",
                            "properties": {
                                "text": "Capture KCC Details",
                                "variant": "h6",
                                "color": "primary",
                                "sx": {"fontWeight": "bold", "mb": 3}
                            }
                        },
                        {
                            "id": "customer_list",
                            "component_type": "CustomerList",
                            "properties": {
                                "sx": {"mb": 3}
                            }
                        }
                    ]
                }
            ]
        },
        "land-details": {
            "id": "ui_land_details_001",
            "screen_id": "land_details_screen",
            "ui_components": [
                {
                    "id": "land_container",
                    "component_type": "Container",
                    "properties": {"padding": "24px"},
                    "children": [
                        {
                            "id": "land_title",
                            "component_type": "Text",
                            "properties": {
                                "text": "Capture Land Details",
                                "variant": "h6",
                                "color": "primary",
                                "sx": {"fontWeight": "bold", "mb": 3}
                            }
                        },
                        {
                            "id": "village_input",
                            "component_type": "Input",
                            "properties": {
                                "label": "Village",
                                "placeholder": "Enter village name",
                                "required": True,
                                "sx": {"mb": 2}
                            }
                        },
                        {
                            "id": "survey_number_input",
                            "component_type": "Input",
                            "properties": {
                                "label": "Survey Number",
                                "placeholder": "Enter survey number",
                                "required": True,
                                "sx": {"mb": 3}
                            }
                        },
                        {
                            "id": "submit_land_button",
                            "component_type": "Button",
                            "properties": {
                                "text": "Submit Application",
                                "variant": "contained",
                                "color": "primary",
                                "fullWidth": True,
                                "action": {
                                    "type": "submit_form",
                                    "action_id": "land-details",
                                    "next_success_action_id": None
                                }
                            }
                        }
                    ]
                }
            ]
        }
    }
    
    # Create the complete workflow schema
    workflow_schema = {
        "action_schema": kcc_action_schema,
        "ui_schema": kcc_ui_schema
    }
    
    print("🏦 Adding Federal Bank KCC Workflow to Database")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        # Check if workflow already exists
        existing_workflow = db.query(Workflow).filter(
            Workflow.bank_name == "federal",
            Workflow.product_type == "kcc"
        ).first()
        
        if existing_workflow:
            print("⚠️  Workflow already exists. Updating...")
            existing_workflow.action_schema = kcc_action_schema
            existing_workflow.ui_schema = kcc_ui_schema
            existing_workflow.api_schema = {}  # Empty for now
            db.commit()
            print("✅ KCC workflow updated successfully!")
        else:
            print("➕ Creating new KCC workflow...")
            new_workflow = Workflow(
                bank_name="federal",
                product_type="kcc",
                action_schema=kcc_action_schema,
                ui_schema=kcc_ui_schema,
                api_schema={}  # Empty for now
            )
            db.add(new_workflow)
            db.commit()
            print("✅ KCC workflow added successfully!")
        
        # Verify the workflow was added
        verification = db.query(Workflow).filter(
            Workflow.bank_name == "federal",
            Workflow.product_type == "kcc"
        ).first()
        
        if verification:
            print(f"✅ Verification successful!")
            print(f"   Bank: {verification.bank_name}")
            print(f"   Product: {verification.product_type}")
            print(f"   Actions: {len(verification.action_schema)}")
            print(f"   UI Screens: {len(verification.ui_schema)}")
            print(f"   Active: {verification.is_active}")
            
            print("\n🎯 KCC Workflow Steps:")
            for i, action in enumerate(verification.action_schema, 1):
                print(f"   {i:2d}. {action['stage_name']} ({action['id']})")
            
            print("\n🚀 Your KCC workflow is now ready!")
            print("   Users can now start KCC applications with:")
            print("   'I want to onboard a customer for federal bank kcc'")
            
        else:
            print("❌ Verification failed - workflow not found in database")
            
    except Exception as e:
        print(f"❌ Error adding KCC workflow: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    add_kcc_workflow()
