# 🚀 Step-by-Step Publishing Commands

Copy and paste these commands to publish your app.

---

## 📱 **BEFORE PUBLISHING**

### **1. Test Everything**
```bash
cd C:\Users\YASHg\OneDrive\Desktop\college_bus_mobile

# Connect device
flutter devices

# Run on device
flutter run

# Test all features:
# - Login
# - Parent dashboard
# - Driver dashboard
# - Live tracking map
# - Push notifications
```

### **2. Update Version**
Edit `pubspec.yaml`:
```yaml
version: 1.0.0+1
```

---

## 🤖 **ANDROID - Google Play Store**

### **Step 1: Create Signing Key**
```bash
# Windows - Create in home directory
cd C:\Users\YASHg

keytool -genkey -v -keystore college_bus.keystore ^
  -keyalg RSA -keysize 2048 -validity 10000 ^
  -alias college_bus_key

# Prompts appear - fill in your info:
# First/Last Name: [Your Name]
# Organization: [Your Company]
# City: [Your City]
# State: [Your State]
# Country: [US]
# Keystore Password: [Create strong password]
# Key Password: [Same as above]
```

### **Step 2: Configure Signing**
Create `C:\Users\YASHg\OneDrive\Desktop\college_bus_mobile\android\key.properties`:
```
storePassword=your_keystore_password_here
keyPassword=your_key_password_here
keyAlias=college_bus_key
storeFile=C:/Users/YASHg/college_bus.keystore
```

### **Step 3: Build Release APK**
```bash
cd C:\Users\YASHg\OneDrive\Desktop\college_bus_mobile

flutter build apk --release

# Output: build/app/outputs/flutter-apk/app-release.apk
```

### **Step 4: Build App Bundle (Recommended for Play Store)**
```bash
flutter build appbundle --release

# Output: build/app/outputs/bundle/release/app-release.aab
```

### **Step 5: Create Google Play Console Account**
1. Go to: https://play.google.com/console
2. Sign in with Google account
3. Pay $25 one-time fee
4. Create new app with name "College Bus Management"

### **Step 6: Upload Build**
1. In Play Console → Releases → Production
2. Click "Create release"
3. Upload the `.aab` file
4. Fill in release notes:
   ```
   Initial launch - College Bus Management app
   
   Features:
   • Real-time GPS bus tracking
   • Live ETA calculation
   • Student attendance system
   • Driver management
   • Push notifications
   • Dark mode support
   ```
5. Review and publish

---

## 🍎 **iOS - Apple App Store**

### **Step 1: Create Apple Developer Account**
1. Go to: https://developer.apple.com
2. Sign in with Apple ID
3. Enroll in Developer Program ($99/year)

### **Step 2: Create App ID & Certificates**
1. Go to Certificates, Identifiers & Profiles
2. Create App ID: `com.yourcompany.collegebusmgmt`
3. Create iOS Distribution Certificate
4. Create App Store Provisioning Profile
5. Download files and import to Xcode

### **Step 3: Configure in Xcode**
```bash
cd C:\Users\YASHg\OneDrive\Desktop\college_bus_mobile
open ios/Runner.xcworkspace
```

**In Xcode:**
1. Select Runner project
2. Go to Signing & Capabilities
3. Select your team
4. Verify bundle ID and provisioning profile

### **Step 4: Build for iOS**
```bash
flutter build ios --release

# Then open in Xcode:
open ios/Runner.xcworkspace

# In Xcode:
# Product → Archive → Distribute App → App Store Connect
```

### **Step 5: Create App Store Connect Entry**
1. Go to: https://appstoreconnect.apple.com
2. Create new app
3. Fill app details (same info as Android)

### **Step 6: Upload Build**
- Upload build through Xcode or Transporter
- Fill app information and screenshots

### **Step 7: Submit for Review**
- Click "Submit for Review"
- Wait 1-2 days for approval

---

## 📊 **After Publishing**

### **Share Download Links**
```
Google Play: https://play.google.com/store/apps/details?id=com.yourcompany.collegebusmgmt
App Store: https://apps.apple.com/app/college-bus-management/id{app-id}
```

### **Monitor Performance**
```bash
# Check analytics in:
# - Google Play Console
# - App Store Connect
# - Firebase Console
```

### **Fix Issues**
```bash
# If critical bug found:
# 1. Fix code
# 2. Update version in pubspec.yaml
# 3. Rebuild: flutter build appbundle --release
# 4. Submit new version
```

---

## 🔄 **Future Updates**

### **Release Version 1.1.0**
```bash
# Edit pubspec.yaml
version: 1.1.0+2

# Rebuild
flutter build appbundle --release
flutter build ios --release

# Upload to both stores
```

---

## 💡 **Tips**

1. **Keep keystore safe** - Backup college_bus.keystore file
2. **Version numbers** - Never decrease, only increase
3. **Test before submit** - No need to resubmit if minor bugs
4. **User feedback** - Respond to reviews promptly
5. **Regular updates** - Update monthly with new features

---

## ✅ **Final Checklist Before Publishing**

```bash
# 1. Clean everything
flutter clean

# 2. Get fresh dependencies
flutter pub get

# 3. Test one more time
flutter run

# 4. Verify app builds
flutter build apk --release
flutter build appbundle --release
flutter build ios --release

# 5. Check sizes
ls -lh build/app/outputs/bundle/release/app-release.aab
ls -lh build/app/outputs/flutter-apk/app-release.apk

# All done! Ready to submit ✅
```

---

**Total time for first publish: ~3 hours**
- Setup & preparation: 1 hour
- Building: 30 minutes
- Account creation: 30 minutes
- App submission: 30 minutes
- Waiting for approval: 1-3 hours

**Good luck! 🚀**

