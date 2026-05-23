"""
 * Tests that dataset has 3 classes and no critical nulls.
"""
import pytest
import pandas as pd

def test_label_distribution():
    """
     * Test that the label column exists and contains exactly 3 distinct classes.
    """
    # // Read the active dataset
    df = pd.read_csv('data/raw/project.csv')
    # // Assert label column is present
    assert 'label' in df.columns, "label column missing"
    classes = df['label'].nunique()
    # // Assert exactly 3 classes exist
    assert classes == 3, f"Expected 3 classes, got {classes}. All labels may be 0."

def test_no_null_labels():
    """
     * Test that there are no null values in the label column.
    """
    # // Read the active dataset
    df = pd.read_csv('data/raw/project.csv')
    null_labels = df['label'].isnull().sum()
    # // Assert no null labels
    assert null_labels == 0, f"{null_labels} null labels found"

def test_class_balance():
    """
     * Test that each class has at least 50 samples to support proper training.
    """
    # // Read the active dataset
    df = pd.read_csv('data/raw/project.csv')
    counts = df['label'].value_counts()
    min_class = counts.min()
    # // Assert minimum class count is >= 50
    assert min_class >= 50, f"Smallest class has only {min_class} samples. Need at least 50 per class."
