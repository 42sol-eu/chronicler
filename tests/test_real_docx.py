"""Integration test for reading a real DOCX file."""

import pytest
from pathlib import Path

from src.chronicler.docx_reader import DocxPropertiesReader, DocumentProperties


class TestRealDocxFile:
    """Test reading properties from a real DOCX file."""
    
    @pytest.fixture
    def docx_file_path(self):
        """Fixture providing the path to the test DOCX file."""
        test_file = Path(__file__).parent / "STMA4000D0001__SW_QSP_B__2025-08-21.docx"
        if not test_file.exists():
            pytest.skip(f"Test DOCX file not found: {test_file}")
        return test_file
    
    def test_read_real_docx_file(self, docx_file_path):
        """Test reading properties from the real DOCX file."""
        reader = DocxPropertiesReader(docx_file_path)
        
        # This should not raise an exception
        props = reader.read_properties()
        
        # Verify we got a DocumentProperties object
        assert isinstance(props, DocumentProperties)
        
        # Print properties for debugging (will show in verbose test output)
        print(f"\n--- Document Properties for {docx_file_path.name} ---")
        print(f"Title: {props.title}")
        print(f"Author: {props.author}")
        print(f"Subject: {props.subject}")
        print(f"Keywords: {props.keywords}")
        print(f"Comments: {props.comments}")
        print(f"Category: {props.category}")
        print(f"Created: {props.created}")
        print(f"Modified: {props.modified}")
        print(f"Last Modified By: {props.last_modified_by}")
        print(f"Custom Properties Count: {len(props.custom_properties)}")
        
        if props.custom_properties:
            print("--- Custom Properties/Variables ---")
            for name, value in props.custom_properties.items():
                print(f"  {name}: {value} (type: {type(value).__name__})")
    
    def test_get_variable_names_real_file(self, docx_file_path):
        """Test getting variable names from the real DOCX file."""
        reader = DocxPropertiesReader(docx_file_path)
        var_names = reader.get_variable_names()
        
        # Should return a list (even if empty)
        assert isinstance(var_names, list)
        
        print(f"\n--- Variable Names in {docx_file_path.name} ---")
        if var_names:
            for name in var_names:
                print(f"  - {name}")
        else:
            print("  No custom variables found")
    
    def test_get_variable_values_real_file(self, docx_file_path):
        """Test getting variable values from the real DOCX file."""
        reader = DocxPropertiesReader(docx_file_path)
        var_values = reader.get_variable_values()
        
        # Should return a dict (even if empty)
        assert isinstance(var_values, dict)
        
        print(f"\n--- Variable Values in {docx_file_path.name} ---")
        if var_values:
            for name, value in var_values.items():
                print(f"  {name} = {value} (type: {type(value).__name__})")
        else:
            print("  No custom variables found")
    
    def test_get_all_properties_dict_real_file(self, docx_file_path):
        """Test getting all properties as a dictionary from the real DOCX file."""
        reader = DocxPropertiesReader(docx_file_path)
        all_props = reader.get_all_properties_dict()
        
        # Should return a dict
        assert isinstance(all_props, dict)
        
        # Should contain standard property keys
        expected_keys = [
            'title', 'author', 'subject', 'keywords', 'comments', 
            'category', 'created', 'modified', 'last_modified_by'
        ]
        
        for key in expected_keys:
            assert key in all_props, f"Missing standard property: {key}"
        
        print(f"\n--- All Properties Dictionary for {docx_file_path.name} ---")
        for key, value in all_props.items():
            if value is not None:
                print(f"  {key}: {value}")
    
    def test_specific_variable_lookup_real_file(self, docx_file_path):
        """Test looking up specific variables from the real DOCX file."""
        reader = DocxPropertiesReader(docx_file_path)
        
        # Get all variable names first
        var_names = reader.get_variable_names()
        
        print(f"\n--- Testing Variable Lookup in {docx_file_path.name} ---")
        
        if var_names:
            # Test getting the first variable
            first_var = var_names[0]
            value = reader.get_variable(first_var)
            print(f"  Variable '{first_var}' = {value}")
            assert value is not None or reader.get_variable_values()[first_var] is None
        
        # Test getting a non-existent variable
        non_existent = reader.get_variable("non_existent_variable_12345")
        assert non_existent is None
        print(f"  Non-existent variable lookup returned: {non_existent}")
    
    def test_document_metadata_validation(self, docx_file_path):
        """Test validation of document metadata from the real file."""
        reader = DocxPropertiesReader(docx_file_path)
        props = reader.read_properties()
        
        print(f"\n--- Document Metadata Validation for {docx_file_path.name} ---")
        
        # File should have been created/modified
        if props.created:
            print(f"  Document created: {props.created}")
            assert props.created is not None
        
        if props.modified:
            print(f"  Document modified: {props.modified}")
            assert props.modified is not None
        
        # Check if the filename suggests this is a technical document
        filename = docx_file_path.name
        if "STMA" in filename:
            print(f"  Appears to be a technical document (contains 'STMA')")
        
        if "QSP" in filename:
            print(f"  Appears to be a QSP document (contains 'QSP')")
        
        if "2025-08-21" in filename:
            print(f"  Document dated 2025-08-21 based on filename")
    
    def test_error_handling_with_real_file(self, docx_file_path):
        """Test that the reader handles the real file without errors."""
        # This should not raise any exceptions
        reader = DocxPropertiesReader(docx_file_path)
        
        # Test all methods to ensure they work
        props = reader.read_properties()
        var_names = reader.get_variable_names()
        var_values = reader.get_variable_values()
        all_props = reader.get_all_properties_dict()
        
        # All should return valid objects
        assert props is not None
        assert isinstance(var_names, list)
        assert isinstance(var_values, dict)
        assert isinstance(all_props, dict)
        
        print(f"\n--- Error Handling Test Passed for {docx_file_path.name} ---")
        print(f"  Successfully read {len(all_props)} total properties")
        print(f"  Found {len(var_names)} custom variables")
    
    def test_debug_document_structure(self, docx_file_path):
        """Debug the document structure to understand how variables are stored."""
        reader = DocxPropertiesReader(docx_file_path)
        debug_info = reader.debug_document_structure()
        
        print(f"\n--- Document Structure Debug for {docx_file_path.name} ---")
        print(f"Parts found in document:")
        for part in debug_info.get('parts_found', []):
            print(f"  - {part}")
        
        print(f"\nXML samples from relevant parts:")
        for part_name, xml_sample in debug_info.get('xml_samples', {}).items():
            print(f"  {part_name}:")
            print(f"    {xml_sample[:200]}..." if len(xml_sample) > 200 else f"    {xml_sample}")
        
        print(f"\nDocVar search attempts:")
        for attempt in debug_info.get('docvars_attempts', []):
            print(f"  - {attempt}")
        
        # Print other debug info
        if 'core_properties_available' in debug_info:
            print(f"\nCore properties available: {debug_info['core_properties_available']}")
        
        if 'custom_properties_available' in debug_info:
            print(f"Custom properties available: {debug_info['custom_properties_available']}")
            print(f"Custom properties count: {debug_info.get('custom_props_count', 0)}")
        
        if 'error' in debug_info:
            print(f"\nError during debug: {debug_info['error']}")
