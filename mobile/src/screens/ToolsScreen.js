import React, { useState } from 'react';
import { View, ScrollView, StyleSheet, Alert } from 'react-native';
import { Text, Card, Button, SegmentedButtons, ActivityIndicator } from 'react-native-paper';
import DocumentPicker from 'react-native-document-picker';
import RNFS from 'react-native-fs';
import Share from 'react-native-share';
import { useAuth } from '../services/AuthService';

const ToolsScreen = ({ route }) => {
  const { selectedTool } = route.params || {};
  const { token, API_BASE_URL } = useAuth();
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [processing, setProcessing] = useState(false);
  const [activeTool, setActiveTool] = useState(selectedTool || 'merge');

  const tools = [
    { value: 'merge', label: 'Merge' },
    { value: 'split', label: 'Split' },
    { value: 'compress', label: 'Compress' },
    { value: 'ocr', label: 'OCR' },
    { value: 'extract', label: 'Extract' },
    { value: 'batch', label: 'Batch' },
  ];

  const pickFiles = async () => {
    try {
      const results = await DocumentPicker.pick({
        type: [DocumentPicker.types.pdf],
        allowMultiSelection: activeTool === 'merge' || activeTool === 'batch',
      });
      setSelectedFiles(results);
    } catch (err) {
      if (!DocumentPicker.isCancel(err)) {
        Alert.alert('Error', 'Failed to pick files');
      }
    }
  };

  const processFiles = async () => {
    if (selectedFiles.length === 0) {
      Alert.alert('Error', 'Please select files first');
      return;
    }

    if (!token) {
      Alert.alert('Error', 'Please login to use this feature');
      return;
    }

    setProcessing(true);

    try {
      const formData = new FormData();
      
      selectedFiles.forEach((file, index) => {
        formData.append('files', {
          uri: file.uri,
          type: file.type,
          name: file.name,
        });
      });

      let endpoint = '';
      let additionalData = {};

      switch (activeTool) {
        case 'merge':
          endpoint = '/pdf/merge';
          break;
        case 'split':
          endpoint = '/pdf/split';
          additionalData.pages = '1-5'; // Example page range
          break;
        case 'compress':
          endpoint = '/pdf/compress-advanced';
          additionalData.preset = 'balanced';
          break;
        case 'ocr':
          endpoint = '/pdf/ocr-advanced';
          additionalData.languages = ['eng'];
          break;
        case 'extract':
          endpoint = '/pdf/extract-text-advanced';
          additionalData.format = 'txt';
          break;
        case 'batch':
          endpoint = '/pdf/batch-process';
          additionalData.operation = 'compress';
          additionalData.preset = 'balanced';
          break;
      }

      // Add additional form data
      Object.keys(additionalData).forEach(key => {
        formData.append(key, additionalData[key]);
      });

      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'multipart/form-data',
        },
        body: formData,
      });

      if (response.ok) {
        if (activeTool === 'extract' || activeTool === 'batch') {
          // Text response
          const text = await response.text();
          Alert.alert('Success', `Extracted text:\n${text.substring(0, 200)}...`);
        } else {
          // PDF response - save and share
          const blob = await response.blob();
          const fileName = `processed_${Date.now()}.pdf`;
          const filePath = `${RNFS.DocumentDirectoryPath}/${fileName}`;
          
          // Convert blob to base64 and save
          const reader = new FileReader();
          reader.onloadend = async () => {
            const base64data = reader.result.split(',')[1];
            await RNFS.writeFile(filePath, base64data, 'base64');
            
            // Share the file
            const shareOptions = {
              title: 'Processed PDF',
              url: `file://${filePath}`,
              type: 'application/pdf',
            };
            
            Share.open(shareOptions).catch(() => {
              Alert.alert('Success', `File saved to: ${filePath}`);
            });
          };
          reader.readAsDataURL(blob);
        }
        
        setSelectedFiles([]);
      } else {
        const errorData = await response.json();
        Alert.alert('Error', errorData.error || 'Processing failed');
      }
    } catch (error) {
      Alert.alert('Error', 'Network error occurred');
    } finally {
      setProcessing(false);
    }
  };

  const getToolDescription = () => {
    const descriptions = {
      merge: 'Combine multiple PDF files into a single document',
      split: 'Extract specific pages from a PDF document',
      compress: 'Reduce PDF file size with advanced compression',
      ocr: 'Extract text from scanned documents using OCR',
      extract: 'Extract text content in various formats',
      batch: 'Process multiple files with the same operation',
    };
    return descriptions[activeTool] || 'Select a tool to get started';
  };

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>PDF Tools</Text>
      
      <Card style={styles.toolCard}>
        <Card.Content>
          <Text style={styles.sectionTitle}>Select Tool</Text>
          <SegmentedButtons
            value={activeTool}
            onValueChange={setActiveTool}
            buttons={tools.slice(0, 3)}
            style={styles.segmentedButtons}
          />
          <SegmentedButtons
            value={activeTool}
            onValueChange={setActiveTool}
            buttons={tools.slice(3)}
            style={styles.segmentedButtons}
          />
          <Text style={styles.description}>{getToolDescription()}</Text>
        </Card.Content>
      </Card>

      <Card style={styles.fileCard}>
        <Card.Content>
          <Text style={styles.sectionTitle}>Select Files</Text>
          <Button
            mode="outlined"
            onPress={pickFiles}
            icon="file-pdf-box"
            style={styles.pickButton}
          >
            {selectedFiles.length > 0 
              ? `${selectedFiles.length} file(s) selected` 
              : 'Pick PDF Files'
            }
          </Button>
          
          {selectedFiles.length > 0 && (
            <View style={styles.fileList}>
              {selectedFiles.map((file, index) => (
                <Text key={index} style={styles.fileName}>
                  {file.name}
                </Text>
              ))}
            </View>
          )}
        </Card.Content>
      </Card>

      <Card style={styles.processCard}>
        <Card.Content>
          <Text style={styles.sectionTitle}>Process</Text>
          <Button
            mode="contained"
            onPress={processFiles}
            disabled={processing || selectedFiles.length === 0}
            icon={processing ? undefined : 'play'}
            style={styles.processButton}
          >
            {processing ? 'Processing...' : `Process with ${activeTool}`}
          </Button>
          
          {processing && (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" />
              <Text style={styles.loadingText}>Processing your files...</Text>
            </View>
          )}
        </Card.Content>
      </Card>

      <Card style={styles.infoCard}>
        <Card.Content>
          <Text style={styles.sectionTitle}>Features</Text>
          <Text style={styles.featureText}>
            • Advanced OCR with 20+ languages{'\n'}
            • Multiple compression presets{'\n'}
            • Batch processing support{'\n'}
            • Secure cloud processing{'\n'}
            • Export in multiple formats
          </Text>
        </Card.Content>
      </Card>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
    padding: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#212529',
    marginBottom: 16,
  },
  toolCard: {
    marginBottom: 16,
    elevation: 2,
  },
  fileCard: {
    marginBottom: 16,
    elevation: 2,
  },
  processCard: {
    marginBottom: 16,
    elevation: 2,
  },
  infoCard: {
    marginBottom: 16,
    elevation: 2,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#212529',
    marginBottom: 12,
  },
  segmentedButtons: {
    marginBottom: 8,
  },
  description: {
    fontSize: 14,
    color: '#6c757d',
    marginTop: 8,
    fontStyle: 'italic',
  },
  pickButton: {
    marginBottom: 12,
  },
  fileList: {
    marginTop: 8,
  },
  fileName: {
    fontSize: 14,
    color: '#495057',
    marginBottom: 4,
    paddingLeft: 8,
  },
  processButton: {
    marginBottom: 12,
  },
  loadingContainer: {
    alignItems: 'center',
    marginTop: 16,
  },
  loadingText: {
    marginTop: 8,
    color: '#6c757d',
  },
  featureText: {
    fontSize: 14,
    color: '#495057',
    lineHeight: 20,
  },
});

export default ToolsScreen;