"""Tests for the docx-check CLI command."""

import json
from unittest.mock import Mock, patch
import pytest
from click.testing import CliRunner

from src.chronicler.__main__ import cli


class TestDocxCheckCommand:
    """Test the docx-check CLI command."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_docx_check_help(self):
        """Test the help output for docx-check command."""
        result = self.runner.invoke(cli, ['docx-check', '--help'])
        assert result.exit_code == 0
        assert 'Check for required document variables' in result.output
        assert 'ID, Revision,' in result.output  # Split across lines in help text
        assert 'Dokumententyp' in result.output
    
    @patch('src.chronicler.__main__.DocxPropertiesReader')
    def test_docx_check_all_variables_found_table(self, mock_reader_class):
        """Test docx-check with all required variables present (table format)."""
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
            
            result = self.runner.invoke(cli, ['docx-check', 'test.docx'])
            
            assert result.exit_code == 0
            assert '✓ Found' in result.output
            assert 'All 8 required variables found!' in result.output
    
    @patch('src.chronicler.__main__.DocxPropertiesReader')
    def test_docx_check_missing_variables_table(self, mock_reader_class):
        """Test docx-check with some variables missing (table format)."""
        # Mock the reader
        mock_reader = Mock()
        mock_reader_class.return_value = mock_reader
        
        # Mock only some variables being present
        mock_reader.get_variable_values.return_value = {
            "ID": "STMA4000D001",
            "Revision": "B",
            "Status": "Freigegeben"
            # Missing: Dokumententyp, Projekt, Freigeber, Freigabedatum, Klassifizierung
        }
        
        with self.runner.isolated_filesystem():
            # Create a dummy file
            with open('test.docx', 'w') as f:
                f.write('dummy')
            
            result = self.runner.invoke(cli, ['docx-check', 'test.docx'])
            
            assert result.exit_code == 0
            assert '✓ Found' in result.output
            assert '✗ Missing' in result.output
            assert '3/8 variables found. 5 missing.' in result.output
    
    @patch('src.chronicler.__main__.DocxPropertiesReader')
    def test_docx_check_verbose_table(self, mock_reader_class):
        """Test docx-check with verbose flag (table format)."""
        # Mock the reader
        mock_reader = Mock()
        mock_reader_class.return_value = mock_reader
        
        mock_reader.get_variable_values.return_value = {
            "ID": "STMA4000D001",
            "Revision": "B"
        }
        
        with self.runner.isolated_filesystem():
            # Create a dummy file
            with open('test.docx', 'w') as f:
                f.write('dummy')
            
            result = self.runner.invoke(cli, ['docx-check', '--verbose', 'test.docx'])
            
            assert result.exit_code == 0
            assert 'STMA4000D001' in result.output  # Should show actual values
            assert 'B' in result.output
    
    @patch('src.chronicler.__main__.DocxPropertiesReader')
    def test_docx_check_json_format(self, mock_reader_class):
        """Test docx-check with JSON output format."""
        # Mock the reader
        mock_reader = Mock()
        mock_reader_class.return_value = mock_reader
        
        mock_reader.get_variable_values.return_value = {
            "ID": "STMA4000D001",
            "Revision": "B",
            "Status": "Freigegeben"
        }
        
        with self.runner.isolated_filesystem():
            # Create a dummy file
            with open('test.docx', 'w') as f:
                f.write('dummy')
            
            result = self.runner.invoke(cli, ['docx-check', '--format', 'json', 'test.docx'])
            
            assert result.exit_code == 0
            
            # Parse JSON output
            output_data = json.loads(result.output)
            
            assert output_data['file'] == 'test.docx'
            assert output_data['summary']['found'] == 3
            assert output_data['summary']['total'] == 8
            assert output_data['summary']['success_rate'] == 37.5
            assert output_data['summary']['all_found'] == False
            
            # Check individual variables
            assert output_data['variables']['ID']['exists'] == True
            assert output_data['variables']['Revision']['exists'] == True
            assert output_data['variables']['Dokumententyp']['exists'] == False
    
    @patch('src.chronicler.__main__.DocxPropertiesReader')
    def test_docx_check_json_verbose(self, mock_reader_class):
        """Test docx-check with JSON format and verbose flag."""
        # Mock the reader
        mock_reader = Mock()
        mock_reader_class.return_value = mock_reader
        
        mock_reader.get_variable_values.return_value = {
            "ID": "STMA4000D001",
            "Revision": "B"
        }
        
        with self.runner.isolated_filesystem():
            # Create a dummy file
            with open('test.docx', 'w') as f:
                f.write('dummy')
            
            result = self.runner.invoke(cli, ['docx-check', '--format', 'json', '--verbose', 'test.docx'])
            
            assert result.exit_code == 0
            
            # Parse JSON output
            output_data = json.loads(result.output)
            
            # Should include values for existing variables
            assert output_data['variables']['ID']['value'] == 'STMA4000D001'
            assert output_data['variables']['Revision']['value'] == 'B'
    
    def test_docx_check_nonexistent_file(self):
        """Test docx-check with non-existent file."""
        result = self.runner.invoke(cli, ['docx-check', 'nonexistent.docx'])
        
        assert result.exit_code == 2  # Click validation error
        assert 'does not exist' in result.output
    
    @patch('src.chronicler.__main__.DocxPropertiesReader')
    def test_docx_check_reader_exception(self, mock_reader_class):
        """Test docx-check when DocxPropertiesReader raises an exception."""
        # Mock the reader to raise an exception
        mock_reader_class.side_effect = Exception("Test error")
        
        with self.runner.isolated_filesystem():
            # Create a dummy file
            with open('test.docx', 'w') as f:
                f.write('dummy')
            
            result = self.runner.invoke(cli, ['docx-check', 'test.docx'])
            
            assert result.exit_code == 1  # Abort
            assert 'Error reading file' in result.output
