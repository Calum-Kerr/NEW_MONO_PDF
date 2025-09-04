# PDF Tools Mobile App

A React Native mobile application for the PDF Tools platform, providing comprehensive PDF processing capabilities on mobile devices.

## Features

### Core PDF Operations
- **Merge PDFs**: Combine multiple PDF files into one
- **Split PDFs**: Extract specific pages from documents
- **Advanced Compression**: Reduce file size with multiple presets
- **OCR Text Extraction**: Extract text from scanned documents with 20+ language support
- **Batch Processing**: Process multiple files simultaneously

### Advanced Features
- **Real-time Analytics**: Track usage patterns and performance
- **Cloud Synchronization**: Secure processing via cloud APIs
- **Multiple Export Formats**: Support for PDF, TXT, JSON, XML outputs
- **User Account Management**: Login, registration, and profile management
- **API Integration**: Full integration with the PDF Tools platform API

## Technology Stack

- **Framework**: React Native with Expo
- **UI Components**: React Native Paper (Material Design)
- **Navigation**: React Navigation 6
- **File Handling**: React Native Document Picker, File System
- **Sharing**: React Native Share
- **Authentication**: JWT-based authentication
- **State Management**: React Context API

## Prerequisites

- Node.js (v16 or higher)
- npm or yarn
- Expo CLI (`npm install -g expo-cli`)
- iOS Simulator (for iOS development)
- Android Studio and Android SDK (for Android development)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd NEW_MONO_PDF/mobile
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Configure API endpoint**:
   - Edit `app.json` and update the `extra.apiUrl` field
   - Or update the `API_BASE_URL` in `src/services/AuthService.js`

## Development

### Start the development server:
```bash
npm start
```

### Run on specific platforms:
```bash
# iOS Simulator
npm run ios

# Android Emulator
npm run android

# Web browser
npm run web
```

### Building for production:
```bash
# Android APK
expo build:android

# iOS IPA
expo build:ios
```

## Project Structure

```
mobile/
├── App.js                          # Main app component
├── app.json                        # Expo configuration
├── package.json                    # Dependencies and scripts
└── src/
    ├── components/                 # Reusable UI components
    ├── screens/                    # Main application screens
    │   ├── HomeScreen.js          # Dashboard and quick actions
    │   ├── ToolsScreen.js         # PDF processing tools
    │   ├── AnalyticsScreen.js     # Usage analytics
    │   └── AccountScreen.js       # User account management
    ├── services/                   # API and business logic
    │   └── AuthService.js         # Authentication service
    └── utils/                      # Helper functions
```

## Features Overview

### Home Screen
- Welcome dashboard with quick action buttons
- Feature highlights and platform overview
- Direct navigation to popular tools

### Tools Screen
- Complete PDF processing toolkit
- File picker with multi-selection support
- Real-time processing with progress indicators
- Result sharing and export capabilities

### Analytics Screen
- Usage statistics and insights
- Performance metrics
- Activity tracking by timeframe
- Visual data representation

### Account Screen
- User profile management
- Subscription status and usage quotas
- Settings and preferences
- Support and help resources

## API Integration

The mobile app integrates with the PDF Tools platform API for:

- **Authentication**: User login and registration
- **PDF Processing**: All PDF operations via secure endpoints
- **Analytics**: Usage tracking and reporting
- **File Management**: Secure file upload and download

### API Configuration

Update the API base URL in `src/services/AuthService.js`:

```javascript
const API_BASE_URL = 'https://your-api-domain.com/api';
```

## Security Features

- **JWT Authentication**: Secure token-based authentication
- **API Key Support**: Enterprise API key integration
- **Secure File Handling**: Temporary file management
- **Privacy Controls**: User data protection settings

## Platform-Specific Features

### iOS
- Native iOS design patterns
- iPad support with adaptive UI
- iOS file picker integration
- Share sheet integration

### Android
- Material Design components
- Android file system integration
- Share intent support
- Adaptive icons

## Development Guidelines

### Code Structure
- Use functional components with hooks
- Implement proper error handling
- Follow React Native best practices
- Maintain consistent styling

### Testing
```bash
# Run tests (when implemented)
npm test
```

### Debugging
- Use React Native Debugger
- Expo Developer Tools
- Console logging for development

## Deployment

### Expo Managed Workflow
1. Build with Expo Build Service
2. Publish to app stores via Expo
3. OTA updates for JavaScript changes

### Ejected/Bare Workflow
1. Build native apps with Xcode/Android Studio
2. Handle native dependencies manually
3. Full control over native configuration

## Environment Variables

Create a `.env` file in the mobile directory:

```
API_BASE_URL=https://your-api-domain.com/api
SENTRY_DSN=your_sentry_dsn_here
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test on both iOS and Android
5. Submit a pull request

## Performance Optimization

- **Lazy Loading**: Screens loaded on demand
- **Image Optimization**: Compressed assets
- **Memory Management**: Proper cleanup of resources
- **Network Optimization**: Request caching and retries

## Accessibility

- **Screen Reader Support**: VoiceOver and TalkBack compatibility
- **High Contrast**: Support for accessibility themes
- **Large Text**: Dynamic font sizing support
- **Keyboard Navigation**: Full keyboard accessibility

## Troubleshooting

### Common Issues

1. **Metro bundler issues**: Clear cache with `expo start -c`
2. **Android build failures**: Check Android SDK configuration
3. **iOS simulator issues**: Reset simulator
4. **Network errors**: Verify API endpoint configuration

### Debug Steps
1. Check console logs
2. Verify network connectivity
3. Test on different devices/simulators
4. Check API endpoint responses

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For technical support:
- Create an issue in the repository
- Contact the development team
- Check the troubleshooting guide

## Roadmap

### Upcoming Features
- **Offline Mode**: Basic operations without internet
- **Dark Theme**: Complete dark mode support
- **Advanced OCR**: More language support and accuracy
- **Collaboration**: Share and collaborate on documents
- **Cloud Storage**: Integration with cloud storage providers