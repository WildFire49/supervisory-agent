import json
import os
import sys
from sqlalchemy.exc import IntegrityError

# Add the project root to the Python path to allow for absolute imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.core.database import SessionLocal, Workflow, create_tables

def seed_database():
    """
    Seeds the database with initial workflow data from a JSON file.
    """
    # Create tables if they don't exist
    print("Initializing database and creating tables if they don't exist...")
    create_tables()
    print("Database tables are ready.")

    # Load data from JSON file
    data_file_path = os.path.join(os.path.dirname(__file__), 'data', 'fed_jlg.json')
    try:
        with open(data_file_path, 'r') as f:
            workflow_data = json.load(f)
        print(f"Loaded workflow data from {data_file_path}")
    except FileNotFoundError:
        print(f"Error: Data file not found at {data_file_path}. Please ensure it exists.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {data_file_path}. Please check its format.")
        return

    db = SessionLocal()
    try:
        # Check if the workflow already exists to prevent duplicates
        existing_workflow = db.query(Workflow).filter_by(
            bank_name=workflow_data['bank_name'],
            product_type=workflow_data['product_type']
        ).first()

        if existing_workflow:
            print(f"Workflow for '{workflow_data['bank_name']} - {workflow_data['product_type']}' already exists. Updating it.")
            existing_workflow.bank_name = workflow_data['bank_name']
            existing_workflow.product_type = workflow_data['product_type']
            existing_workflow.action_schema = workflow_data['action_schema']
            existing_workflow.ui_schema = workflow_data['ui_schema']
            existing_workflow.api_schema = workflow_data['api_schema']
            existing_workflow.is_active = True
            db.commit()
            print(f"Successfully updated workflow for '{existing_workflow.bank_name} - {existing_workflow.product_type}'.")
        else:
            new_workflow = Workflow(
                bank_name=workflow_data['bank_name'],
                product_type=workflow_data['product_type'],
                action_schema=workflow_data['action_schema'],
                ui_schema=workflow_data['ui_schema'],
                api_schema=workflow_data['api_schema'],
                is_active=True
            )
            db.add(new_workflow)
            db.commit()
            print(f"Successfully seeded workflow for '{new_workflow.bank_name} - {new_workflow.product_type}'.")

    except IntegrityError:
        db.rollback()
        print("Database integrity error. This might happen in a race condition. The workflow likely already exists.")
    except Exception as e:
        db.rollback()
        print(f"An unexpected error occurred: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("--- Starting Database Seeding ---")
    seed_database()
    print("--- Database Seeding Finished ---")
