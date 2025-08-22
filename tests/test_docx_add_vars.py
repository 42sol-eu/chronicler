"""Tests for the docx-add-vars CLI command."""

import json
import tempfile
import shutil
from unittest.mock import Mock, patch
import pytest
from click.testing import CliRunner

from src.chronicler.__main__ import cli
from src.chronicler.docx_reader import DocxPropertiesReader


class TestDocxAddVarsCommand:
    """Test the docx-add-vars CLI command."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_docx_add_vars_help(self):
        """Test the help output for docx-add-vars command."""
        result = self.runner.invoke(cli, ['docx-add-vars', '--help'])
        assert result.exit_code == 0
        assert 'Add missing document variables' in result.output
        assert 'ID, Revision, Dokumententyp' in result.output
    
    @patch('src.chronicler.__main__.DocxPropertiesReader')
    def test_docx_add_vars_all_present(self, mock_reader_class):
        """Test docx-add-vars when all variables are already present."""
        # Mock the reader
        mock_reader = Mock()
        mock_reader_class.return_value = mock_reader
        
        # Mock all required variables being present
        mock_reader.get_variable_values.return_value = {
            "ID": "STMA4000D001",
            "Revision": "B", 
            "Dokumententyp": "Planungsdokument",
            "Projekt": "FLIRT_BEMU_PFZ",
            "Freigeber": "D. Plessow",
            "Freigabedatum": "2025-08-21",
            "Status": "Freigegeben",
            "Klassifizierung": "Intern"
        }
        
        with self.runner.isolated_filesystem():
            # Create a dummy file
            with open('test.docx', 'w') as f:
                f.write('dummy')
            
            result = self.runner.invoke(cli, ['docx-add-vars', 'test.docx'])
            
            assert result.exit_code == 0
            assert 'All required variables are already present!' in result.output
    
    def test_docx_add_vars_force_mode(self):
        """Test force mode with existing variables."""
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_file:
            temp_path = temp_file.name
            
        try:
            with patch.object(DocxPropertiesReader, '__init__', return_value=None):
                with patch.object(DocxPropertiesReader, 'get_variable_values') as mock_get_vars:
                    mock_get_vars.return_value = {
                        'ID': 'STMA4000D001',
                        'Revision': 'B',
                        'Dokumententyp': 'QSP',
                        'Projekt': 'Project A',
                        'Freigeber': 'John Doe',
                        'Freigabedatum': '2024-01-01',
                        'Status': 'Released',
                        'Klassifizierung': 'Internal'
                    }
                    
                    runner = CliRunner()
                    result = runner.invoke(cli, ['docx-add-vars', temp_path, '--force'], input='\n\n\n\n\n\n\n\n')
                    
                    assert result.exit_code == 0
                    # In force mode, all variables are shown with current values
                    assert 'current: STMA4000D001' in result.output
                    assert 'current: B' in result.output
                    assert 'Missing variables: 8' in result.output
        finally:
            # Clean up
            import os
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    @patch('src.chronicler.__main__.DocxPropertiesReader')
    def test_docx_add_vars_interactive_skip_all(self, mock_reader_class):
        """Test docx-add-vars interactive mode skipping all variables."""
        # Mock the reader
        mock_reader = Mock()
        mock_reader_class.return_value = mock_reader
        
        # Mock no variables being present
        mock_reader.get_variable_values.return_value = {}
        
        with self.runner.isolated_filesystem():
            # Create a dummy file
            with open('test.docx', 'w') as f:
                f.write('dummy')
            
            # Simulate pressing Enter for all prompts (skip all)
            result = self.runner.invoke(cli, ['docx-add-vars', 'test.docx'], 
                                      input='\n\n\n\n\n\n\n\n')
            
            assert result.exit_code == 0
            assert 'No variables provided. No changes made.' in result.output
    
    @patch('src.chronicler.__main__.DocxPropertiesReader')
    def test_docx_add_vars_interactive_add_some(self, mock_reader_class):
        """Test docx-add-vars interactive mode adding some variables."""
        # Mock the reader
        mock_reader = Mock()
        mock_reader_class.return_value = mock_reader
        
        # Mock no variables being present initially
        mock_reader.get_variable_values.return_value = {}
        mock_reader.add_custom_properties.return_value = 'test.docx'
        
        # Mock the updated reader after adding properties
        updated_mock_reader = Mock()
        updated_mock_reader.get_variable_values.return_value = {
            "ID": "TEST001",
            "Revision": "A"
        }
        
        # Use side_effect to return different instances
        mock_reader_class.side_effect = [mock_reader, updated_mock_reader]
        
        with self.runner.isolated_filesystem():
            # Create a dummy file
            with open('test.docx', 'w') as f:
                f.write('dummy')
            
            # Simulate entering values for ID and Revision, skipping others, confirming, and verifying
            user_input = 'TEST001\nA\n\n\n\n\n\n\ny\ny\n'
            result = self.runner.invoke(cli, ['docx-add-vars', 'test.docx'], input=user_input)
            
            assert result.exit_code == 0
            assert 'Successfully added' in result.output
            assert 'TEST001' in result.output
    
    def test_docx_add_vars_nonexistent_file(self):
        """Test docx-add-vars with non-existent file."""
        result = self.runner.invoke(cli, ['docx-add-vars', 'nonexistent.docx'])
        
        assert result.exit_code == 2  # Click validation error
        assert 'does not exist' in result.output
    
    @patch('src.chronicler.__main__.DocxPropertiesReader')
    def test_docx_add_vars_reader_exception(self, mock_reader_class):
        """Test docx-add-vars when DocxPropertiesReader raises an exception."""
        # Mock the reader to raise an exception
        mock_reader_class.side_effect = Exception("Test error")
        
        with self.runner.isolated_filesystem():
            # Create a dummy file
            with open('test.docx', 'w') as f:
                f.write('dummy')
            
            result = self.runner.invoke(cli, ['docx-add-vars', 'test.docx'])
            
            assert result.exit_code == 1  # Abort
            assert 'Error:' in result.output
    
    @patch('src.chronicler.__main__.DocxPropertiesReader')
    def test_docx_add_vars_batch_mode_not_implemented(self, mock_reader_class):
        """Test docx-add-vars batch mode (not yet implemented)."""
        # Mock the reader
        mock_reader = Mock()
        mock_reader_class.return_value = mock_reader
        mock_reader.get_variable_values.return_value = {}
        
        with self.runner.isolated_filesystem():
            # Create a dummy file
            with open('test.docx', 'w') as f:
                f.write('dummy')
            
            result = self.runner.invoke(cli, ['docx-add-vars', '--batch', 'test.docx'])
            
            assert result.exit_code == 1  # Abort
            assert 'Batch mode not yet implemented' in result.output
    
    @patch('src.chronicler.__main__.DocxPropertiesReader')
    def test_docx_add_vars_with_output_file(self, mock_reader_class):
        """Test docx-add-vars with custom output file."""
        # Mock the reader
        mock_reader = Mock()
        mock_reader_class.return_value = mock_reader
        
        mock_reader.get_variable_values.return_value = {}
        mock_reader.add_custom_properties.return_value = 'output.docx'
        
        # Mock the updated reader
        updated_mock_reader = Mock()
        updated_mock_reader.get_variable_values.return_value = {"ID": "TEST001"}
        mock_reader_class.side_effect = [mock_reader, updated_mock_reader]
        
        with self.runner.isolated_filesystem():
            # Create a dummy file
            with open('test.docx', 'w') as f:
                f.write('dummy')
            
            # Simulate entering one value, confirming, and verifying
            user_input = 'TEST001\n\n\n\n\n\n\n\ny\ny\n'
            result = self.runner.invoke(cli, ['docx-add-vars', '-o', 'output.docx', 'test.docx'], 
                                      input=user_input)
            
            assert result.exit_code == 0
            assert 'output.docx' in result.output

    @patch('src.chronicler.__main__.DocxPropertiesReader')
    def test_docx_add_vars_review_all_mode(self, mock_reader_class):
        """Test review-all mode that shows all variables for review."""
        # Mock the reader
        mock_reader = Mock()
        mock_reader_class.return_value = mock_reader
        
        mock_reader.get_variable_values.return_value = {
            'ID': 'EXISTING001',
            'Revision': 'A', 
            'Status': 'Draft'
            # Missing: Dokumententyp, Projekt, Freigeber, Freigabedatum, Klassifizierung
        }
        mock_reader.add_custom_properties.return_value = 'test.docx'
        
        with self.runner.isolated_filesystem():
            # Create a dummy file
            with open('test.docx', 'w') as f:
                f.write('dummy')
            
            # Update ID, keep Revision, add new Dokumententyp, skip others
            user_input = 'NEW_ID\n\nTestDoc\n\n\n\n\ny\ny\nn\n'
            result = self.runner.invoke(cli, ['docx-add-vars', '--review-all', 'test.docx'], 
                                     input=user_input)
            
            assert result.exit_code == 0
            assert 'Review Mode: All 8 variables' in result.output
            assert 'Current Variable Status:' in result.output
            assert 'Interactive Variable Review:' in result.output
            assert 'Will update: EXISTING001 → NEW_ID' in result.output
            assert 'Keeping current: A' in result.output
            assert 'Will add: TestDoc' in result.output
            mock_reader.add_custom_properties.assert_called_once()

    @patch('src.chronicler.__main__.DocxPropertiesReader')
    def test_docx_add_vars_review_all_batch_mode_error(self, mock_reader_class):
        """Test that review-all mode requires interactive flag."""
        mock_reader = Mock()
        mock_reader_class.return_value = mock_reader
        
        with self.runner.isolated_filesystem():
            # Create a dummy file
            with open('test.docx', 'w') as f:
                f.write('dummy')
            
            result = self.runner.invoke(cli, ['docx-add-vars', '--review-all', '--batch', 'test.docx'])
            
            assert result.exit_code == 1
            assert 'Review all mode requires --interactive flag' in result.output

    @patch('src.chronicler.__main__.DocxPropertiesReader')
    def test_docx_add_vars_review_all_no_changes(self, mock_reader_class):
        """Test review-all mode when user makes no changes."""
        mock_reader = Mock()
        mock_reader_class.return_value = mock_reader
        
        mock_reader.get_variable_values.return_value = {
            'ID': 'TEST001',
            'Revision': 'B'
        }
        
        with self.runner.isolated_filesystem():
            # Create a dummy file
            with open('test.docx', 'w') as f:
                f.write('dummy')
            
            # Press enter for all variables (no changes)
            user_input = '\n\n\n\n\n\n\n\n'
            result = self.runner.invoke(cli, ['docx-add-vars', '--review-all', 'test.docx'], 
                                     input=user_input)
            
            assert result.exit_code == 0
            assert 'No variables provided. No changes made.' in result.output

    @patch('src.chronicler.__main__.DocxPropertiesReader')
    def test_docx_add_vars_review_all_help_message(self, mock_reader_class):
        """Test that normal mode suggests review-all when all variables exist."""
        mock_reader = Mock()
        mock_reader_class.return_value = mock_reader
        
        # All variables present
        mock_reader.get_variable_values.return_value = {
            'ID': 'TEST001',
            'Revision': 'A',
            'Dokumententyp': 'QSP',
            'Projekt': 'TestProject',
            'Freigeber': 'John Doe',
            'Freigabedatum': '2025-08-22',
            'Status': 'Released',
            'Klassifizierung': 'Internal'
        }
        
        with self.runner.isolated_filesystem():
            # Create a dummy file
            with open('test.docx', 'w') as f:
                f.write('dummy')
            
            result = self.runner.invoke(cli, ['docx-add-vars', 'test.docx'])
            
            assert result.exit_code == 0
            assert 'All required variables are already present!' in result.output
            assert 'Use --review-all to review and update all variables' in result.output
