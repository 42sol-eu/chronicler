"""Test cases for DOCX properties reader."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Check if python-docx is available
try:
    from src.chronicler.docx_reader import DocxPropertiesReader, DocumentProperties
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    DocxPropertiesReader = None
    DocumentProperties = None


@pytest.mark.skipif(not DOCX_AVAILABLE, reason="python-docx not available")


class TestDocxPropertiesReader:
    """Test the DOCX properties reader functionality."""
    
    def test_init_with_valid_file(self, tmp_path):
        """Test initialization with a valid DOCX file path."""
        # Create a temporary .docx file
        docx_file = tmp_path / "test.docx"
        docx_file.write_text("dummy content")
        
        reader = DocxPropertiesReader(docx_file)
        assert reader.file_path == docx_file
    
    def test_init_with_nonexistent_file(self):
        """Test initialization with a non-existent file."""
        with pytest.raises(FileNotFoundError):
            DocxPropertiesReader("nonexistent.docx")
    
    def test_init_with_non_docx_file(self, tmp_path):
        """Test initialization with a non-DOCX file."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("dummy content")
        
        with pytest.raises(ValueError, match="File is not a DOCX file"):
            DocxPropertiesReader(txt_file)
    
    @patch('src.chronicler.docx_reader.Document')
    def test_read_properties_success(self, mock_document):
        """Test successful reading of document properties."""
        # Mock the Document and its properties
        mock_doc = Mock()
        mock_core_props = Mock()
        mock_core_props.title = "Test Title"
        mock_core_props.author = "Test Author"
        mock_core_props.subject = "Test Subject"
        mock_core_props.keywords = "test, keywords"
        mock_core_props.comments = "Test comments"
        mock_core_props.category = "Test Category"
        mock_core_props.created = datetime(2025, 1, 1, 12, 0, 0)
        mock_core_props.modified = datetime(2025, 1, 2, 12, 0, 0)
        mock_core_props.last_modified_by = "Test User"
        
        mock_doc.core_properties = mock_core_props
        mock_doc.part.custom_properties = []  # No custom properties
        
        mock_document.return_value = mock_doc
        
        # Create a temporary .docx file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
            tmp_path = Path(tmp.name)
        
        try:
            reader = DocxPropertiesReader(tmp_path)
            props = reader.read_properties()
            
            assert props.title == "Test Title"
            assert props.author == "Test Author"
            assert props.subject == "Test Subject"
            assert props.keywords == "test, keywords"
            assert props.comments == "Test comments"
            assert props.category == "Test Category"
            assert props.created == datetime(2025, 1, 1, 12, 0, 0)
            assert props.modified == datetime(2025, 1, 2, 12, 0, 0)
            assert props.last_modified_by == "Test User"
            assert props.custom_properties == {}
        finally:
            tmp_path.unlink()
    
    @patch('src.chronicler.docx_reader.Document')
    def test_read_custom_properties(self, mock_document):
        """Test reading custom properties from document."""
        # Mock custom properties
        mock_prop1 = Mock()
        mock_prop1.name = "custom_var1"
        mock_prop1.value = "string_value"
        mock_prop1.type = "string"
        
        mock_prop2 = Mock()
        mock_prop2.name = "custom_var2"
        mock_prop2.value = 42
        mock_prop2.type = "number"
        
        mock_doc = Mock()
        mock_doc.core_properties = Mock()
        mock_doc.part.custom_properties = [mock_prop1, mock_prop2]
        
        mock_document.return_value = mock_doc
        
        # Create a temporary .docx file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
            tmp_path = Path(tmp.name)
        
        try:
            reader = DocxPropertiesReader(tmp_path)
            props = reader.read_properties()
            
            assert "custom_var1" in props.custom_properties
            assert props.custom_properties["custom_var1"] == "string_value"
            assert "custom_var2" in props.custom_properties
            assert props.custom_properties["custom_var2"] == 42
        finally:
            tmp_path.unlink()
    
    @patch('src.chronicler.docx_reader.Document')
    def test_get_variable_names(self, mock_document):
        """Test getting variable names."""
        mock_prop = Mock()
        mock_prop.name = "test_var"
        mock_prop.value = "test_value"
        
        mock_doc = Mock()
        mock_doc.core_properties = Mock()
        mock_doc.part.custom_properties = [mock_prop]
        
        mock_document.return_value = mock_doc
        
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
            tmp_path = Path(tmp.name)
        
        try:
            reader = DocxPropertiesReader(tmp_path)
            var_names = reader.get_variable_names()
            
            assert var_names == ["test_var"]
        finally:
            tmp_path.unlink()
    
    @patch('src.chronicler.docx_reader.Document')
    def test_get_variable_values(self, mock_document):
        """Test getting variable values."""
        mock_prop = Mock()
        mock_prop.name = "test_var"
        mock_prop.value = "test_value"
        
        mock_doc = Mock()
        mock_doc.core_properties = Mock()
        mock_doc.part.custom_properties = [mock_prop]
        
        mock_document.return_value = mock_doc
        
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
            tmp_path = Path(tmp.name)
        
        try:
            reader = DocxPropertiesReader(tmp_path)
            var_values = reader.get_variable_values()
            
            assert var_values == {"test_var": "test_value"}
        finally:
            tmp_path.unlink()
    
    @patch('src.chronicler.docx_reader.Document')
    def test_get_variable(self, mock_document):
        """Test getting a specific variable."""
        mock_prop = Mock()
        mock_prop.name = "test_var"
        mock_prop.value = "test_value"
        
        mock_doc = Mock()
        mock_doc.core_properties = Mock()
        mock_doc.part.custom_properties = [mock_prop]
        
        mock_document.return_value = mock_doc
        
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
            tmp_path = Path(tmp.name)
        
        try:
            reader = DocxPropertiesReader(tmp_path)
            
            assert reader.get_variable("test_var") == "test_value"
            assert reader.get_variable("nonexistent") is None
        finally:
            tmp_path.unlink()


@pytest.mark.skipif(not DOCX_AVAILABLE, reason="python-docx not available")
class TestDocumentProperties:
    """Test the DocumentProperties dataclass."""
    
    def test_init_default(self):
        """Test default initialization."""
        props = DocumentProperties()
        
        assert props.title is None
        assert props.author is None
        assert props.custom_properties == {}
    
    def test_init_with_values(self):
        """Test initialization with values."""
        custom_props = {"var1": "value1", "var2": 42}
        props = DocumentProperties(
            title="Test Title",
            author="Test Author",
            custom_properties=custom_props
        )
        
        assert props.title == "Test Title"
        assert props.author == "Test Author"
        assert props.custom_properties == custom_props
