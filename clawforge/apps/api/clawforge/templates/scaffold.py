"""Flutter project scaffold templates.

Provides base project files that every Flutter project needs,
including Android/iOS/Web platform directories.
"""

from typing import Any


def get_pubspec_yaml(app_name: str, description: str) -> str:
    """Generate pubspec.yaml with all required dependencies."""
    snake_name = app_name.lower().replace(" ", "_").replace("-", "_")
    return f'''name: {snake_name}
description: {description}
publish_to: 'none'
version: 1.0.0+1

environment:
  sdk: '>=3.3.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter

  # State Management
  flutter_riverpod: ^2.5.1
  riverpod_annotation: ^2.3.5

  # Navigation
  go_router: ^14.2.0

  # Data & Storage
  freezed_annotation: ^2.4.1
  json_annotation: ^4.9.0
  drift: ^2.18.0
  sqlite3_flutter_libs: ^0.5.21
  path_provider: ^2.1.3
  path: ^1.9.0

  # Networking
  dio: ^5.4.3+1

  # UI
  flutter_animate: ^4.5.0
  cached_network_image: ^3.3.1

  # Utils
  intl: ^0.19.0
  uuid: ^4.4.0

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^4.0.0

  # Code Generation
  build_runner: ^2.4.9
  riverpod_generator: ^2.4.0
  freezed: ^2.5.2
  json_serializable: ^6.8.0
  drift_dev: ^2.18.0

flutter:
  uses-material-design: true

  assets:
    - assets/images/
    - assets/icons/

  # fonts:
  #   - family: CustomFont
  #     fonts:
  #       - asset: assets/fonts/CustomFont-Regular.ttf
'''


def get_analysis_options() -> str:
    """Generate analysis_options.yaml with strict linting."""
    return '''include: package:flutter_lints/flutter.yaml

analyzer:
  errors:
    invalid_annotation_target: ignore
  exclude:
    - "**/*.g.dart"
    - "**/*.freezed.dart"

linter:
  rules:
    prefer_single_quotes: true
    always_use_package_imports: true
    avoid_print: true
    prefer_const_constructors: true
    prefer_const_declarations: true
    prefer_final_fields: true
    prefer_final_locals: true
    require_trailing_commas: true
    sort_constructors_first: true
    unawaited_futures: true
'''


def get_android_build_gradle(app_name: str) -> str:
    """Generate android/app/build.gradle."""
    snake_name = app_name.lower().replace(" ", "_").replace("-", "_")
    return f'''plugins {{
    id "com.android.application"
    id "kotlin-android"
    id "dev.flutter.flutter-gradle-plugin"
}}

def localProperties = new Properties()
def localPropertiesFile = rootProject.file('local.properties')
if (localPropertiesFile.exists()) {{
    localPropertiesFile.withReader('UTF-8') {{ reader ->
        localProperties.load(reader)
    }}
}}

def flutterVersionCode = localProperties.getProperty('flutter.versionCode')
if (flutterVersionCode == null) {{
    flutterVersionCode = '1'
}}

def flutterVersionName = localProperties.getProperty('flutter.versionName')
if (flutterVersionName == null) {{
    flutterVersionName = '1.0'
}}

android {{
    namespace "com.example.{snake_name}"
    compileSdk 36
    ndkVersion flutter.ndkVersion

    compileOptions {{
        sourceCompatibility JavaVersion.VERSION_17
        targetCompatibility JavaVersion.VERSION_17
    }}

    kotlinOptions {{
        jvmTarget = '17'
    }}

    sourceSets {{
        main.java.srcDirs += 'src/main/kotlin'
    }}

    defaultConfig {{
        applicationId "com.example.{snake_name}"
        minSdk 24
        targetSdk 36
        versionCode flutterVersionCode.toInteger()
        versionName flutterVersionName
    }}

    buildTypes {{
        release {{
            signingConfig signingConfigs.debug
        }}
    }}
}}

flutter {{
    source '../..'
}}

dependencies {{}}
'''


def get_android_manifest(app_name: str) -> str:
    """Generate AndroidManifest.xml."""
    display_name = app_name.replace("_", " ").title()
    return f'''<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <application
        android:label="{display_name}"
        android:name="${{applicationName}}"
        android:icon="@mipmap/ic_launcher">
        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:launchMode="singleTop"
            android:theme="@style/LaunchTheme"
            android:configChanges="orientation|keyboardHidden|keyboard|screenSize|smallestScreenSize|locale|layoutDirection|fontScale|screenLayout|density|uiMode"
            android:hardwareAccelerated="true"
            android:windowSoftInputMode="adjustResize">
            <meta-data
              android:name="io.flutter.embedding.android.NormalTheme"
              android:resource="@style/NormalTheme"
              />
            <intent-filter>
                <action android:name="android.intent.action.MAIN"/>
                <category android:name="android.intent.category.LAUNCHER"/>
            </intent-filter>
        </activity>
        <meta-data
            android:name="flutterEmbedding"
            android:value="2" />
    </application>
    <queries>
        <intent>
            <action android:name="android.intent.action.PROCESS_TEXT"/>
            <data android:mimeType="text/plain"/>
        </intent>
    </queries>
</manifest>
'''


def get_android_settings_gradle(app_name: str) -> str:
    """Generate android/settings.gradle."""
    snake_name = app_name.lower().replace(" ", "_").replace("-", "_")
    return f'''pluginManagement {{
    def flutterSdkPath = {{
        def properties = new Properties()
        file("local.properties").withInputStream {{ properties.load(it) }}
        def flutterSdkPath = properties.getProperty("flutter.sdk")
        assert flutterSdkPath != null, "flutter.sdk not set in local.properties"
        return flutterSdkPath
    }}
    settings.ext.flutterSdkPath = flutterSdkPath()

    includeBuild("${{settings.ext.flutterSdkPath}}/packages/flutter_tools/gradle")

    repositories {{
        google()
        mavenCentral()
        gradlePluginPortal()
    }}
}}

plugins {{
    id "dev.flutter.flutter-plugin-loader" version "1.0.0"
    id "com.android.application" version "8.7.0" apply false
    id "org.jetbrains.kotlin.android" version "2.0.21" apply false
}}

include ":app"
'''


def get_android_root_build_gradle() -> str:
    """Generate android/build.gradle."""
    return '''allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.buildDir = '../build'
subprojects {
    project.buildDir = "${rootProject.buildDir}/${project.name}"
}
subprojects {
    project.evaluationDependsOn(':app')
}

tasks.register("clean", Delete) {
    delete rootProject.buildDir
}
'''


def get_android_gradle_wrapper() -> str:
    """Generate gradle-wrapper.properties."""
    return '''distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
distributionUrl=https\\://services.gradle.org/distributions/gradle-8.10.2-all.zip
'''


def get_main_activity_kt(app_name: str) -> str:
    """Generate MainActivity.kt."""
    snake_name = app_name.lower().replace(" ", "_").replace("-", "_")
    return f'''package com.example.{snake_name}

import io.flutter.embedding.android.FlutterActivity

class MainActivity: FlutterActivity()
'''


def get_android_styles_xml() -> str:
    """Generate Android styles.xml."""
    return '''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <!-- Theme applied to the Android Window while the process is starting when the OS's Dark Mode setting is off -->
    <style name="LaunchTheme" parent="@android:style/Theme.Light.NoTitleBar">
        <!-- Show a splash screen on the activity. Automatically removed when
             the Flutter engine draws its first frame -->
        <item name="android:windowBackground">@drawable/launch_background</item>
    </style>
    <!-- Theme applied to the Android Window as soon as the process has started.
         This theme determines the color of the Android Window while your
         Flutter UI initializes, as well as behind your Flutter UI while its
         running.

         This Theme is only used starting with V2 of Flutter's Android embedding. -->
    <style name="NormalTheme" parent="@android:style/Theme.Light.NoTitleBar">
        <item name="android:windowBackground">?android:colorBackground</item>
    </style>
</resources>
'''


def get_android_styles_night_xml() -> str:
    """Generate Android styles.xml for night mode."""
    return '''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <!-- Theme applied to the Android Window while the process is starting when the OS's Dark Mode setting is on -->
    <style name="LaunchTheme" parent="@android:style/Theme.Black.NoTitleBar">
        <!-- Show a splash screen on the activity. Automatically removed when
             the Flutter engine draws its first frame -->
        <item name="android:windowBackground">@drawable/launch_background</item>
    </style>
    <!-- Theme applied to the Android Window as soon as the process has started.
         This theme determines the color of the Android Window while your
         Flutter UI initializes, as well as behind your Flutter UI while its
         running.

         This Theme is only used starting with V2 of Flutter's Android embedding. -->
    <style name="NormalTheme" parent="@android:style/Theme.Black.NoTitleBar">
        <item name="android:windowBackground">?android:colorBackground</item>
    </style>
</resources>
'''


def get_android_launch_background() -> str:
    """Generate Android launch_background.xml."""
    return '''<?xml version="1.0" encoding="utf-8"?>
<!-- Modify this file to customize your launch splash screen -->
<layer-list xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:drawable="?android:colorBackground" />

    <!-- You can insert your own image assets here -->
    <!-- <item>
        <bitmap
            android:gravity="center"
            android:src="@mipmap/launch_image" />
    </item> -->
</layer-list>
'''


def get_web_index_html(app_name: str) -> str:
    """Generate web/index.html."""
    display_name = app_name.replace("_", " ").title()
    return f'''<!DOCTYPE html>
<html>
<head>
  <base href="$FLUTTER_BASE_HREF">
  <meta charset="UTF-8">
  <meta content="IE=Edge" http-equiv="X-UA-Compatible">
  <meta name="description" content="{display_name}">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black">
  <meta name="apple-mobile-web-app-title" content="{display_name}">
  <link rel="apple-touch-icon" href="icons/Icon-192.png">
  <link rel="icon" type="image/png" href="favicon.png"/>
  <title>{display_name}</title>
  <link rel="manifest" href="manifest.json">
</head>
<body>
  <script src="flutter_bootstrap.js" async></script>
</body>
</html>
'''


def get_web_manifest(app_name: str) -> str:
    """Generate web/manifest.json."""
    display_name = app_name.replace("_", " ").title()
    snake_name = app_name.lower().replace(" ", "_").replace("-", "_")
    return f'''{{
    "name": "{display_name}",
    "short_name": "{display_name}",
    "start_url": ".",
    "display": "standalone",
    "background_color": "#0175C2",
    "theme_color": "#0175C2",
    "description": "{display_name} - Built with Flutter",
    "orientation": "portrait-primary",
    "prefer_related_applications": false,
    "icons": [
        {{
            "src": "icons/Icon-192.png",
            "sizes": "192x192",
            "type": "image/png"
        }},
        {{
            "src": "icons/Icon-512.png",
            "sizes": "512x512",
            "type": "image/png"
        }},
        {{
            "src": "icons/Icon-maskable-192.png",
            "sizes": "192x192",
            "type": "image/png",
            "purpose": "maskable"
        }},
        {{
            "src": "icons/Icon-maskable-512.png",
            "sizes": "512x512",
            "type": "image/png",
            "purpose": "maskable"
        }}
    ]
}}
'''


def get_ios_app_delegate() -> str:
    """Generate iOS AppDelegate.swift."""
    return '''import UIKit
import Flutter

@main
@objc class AppDelegate: FlutterAppDelegate {
  override func application(
    _ application: UIApplication,
    didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?
  ) -> Bool {
    GeneratedPluginRegistrant.register(with: self)
    return super.application(application, didFinishLaunchingWithOptions: launchOptions)
  }
}
'''


def get_ios_info_plist(app_name: str) -> str:
    """Generate iOS Info.plist."""
    display_name = app_name.replace("_", " ").title()
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>CFBundleDevelopmentRegion</key>
	<string>$(DEVELOPMENT_LANGUAGE)</string>
	<key>CFBundleDisplayName</key>
	<string>{display_name}</string>
	<key>CFBundleExecutable</key>
	<string>$(EXECUTABLE_NAME)</string>
	<key>CFBundleIdentifier</key>
	<string>$(PRODUCT_BUNDLE_IDENTIFIER)</string>
	<key>CFBundleInfoDictionaryVersion</key>
	<string>6.0</string>
	<key>CFBundleName</key>
	<string>{display_name}</string>
	<key>CFBundlePackageType</key>
	<string>APPL</string>
	<key>CFBundleShortVersionString</key>
	<string>$(FLUTTER_BUILD_NAME)</string>
	<key>CFBundleSignature</key>
	<string>????</string>
	<key>CFBundleVersion</key>
	<string>$(FLUTTER_BUILD_NUMBER)</string>
	<key>LSRequiresIPhoneOS</key>
	<true/>
	<key>UILaunchStoryboardName</key>
	<string>LaunchScreen</string>
	<key>UIMainStoryboardFile</key>
	<string>Main</string>
	<key>UISupportedInterfaceOrientations</key>
	<array>
		<string>UIInterfaceOrientationPortrait</string>
		<string>UIInterfaceOrientationLandscapeLeft</string>
		<string>UIInterfaceOrientationLandscapeRight</string>
	</array>
	<key>UISupportedInterfaceOrientations~ipad</key>
	<array>
		<string>UIInterfaceOrientationPortrait</string>
		<string>UIInterfaceOrientationPortraitUpsideDown</string>
		<string>UIInterfaceOrientationLandscapeLeft</string>
		<string>UIInterfaceOrientationLandscapeRight</string>
	</array>
	<key>CADisableMinimumFrameDurationOnPhone</key>
	<true/>
	<key>UIApplicationSupportsIndirectInputEvents</key>
	<true/>
</dict>
</plist>
'''


def get_ios_podfile() -> str:
    """Generate iOS Podfile."""
    return '''# Uncomment this line to define a global platform for your project
platform :ios, '12.0'

# CocoaPods analytics sends network stats synchronously affecting flutter build latency.
ENV['COCOAPODS_DISABLE_STATS'] = 'true'

project 'Runner', {
  'Debug' => :debug,
  'Profile' => :release,
  'Release' => :release,
}

def flutter_root
  generated_xcode_build_settings_path = File.expand_path(File.join('..', 'Flutter', 'Generated.xcconfig'), __FILE__)
  unless File.exist?(generated_xcode_build_settings_path)
    raise "#{generated_xcode_build_settings_path} must exist. If you're running pod install manually, make sure flutter pub get is executed first"
  end

  File.foreach(generated_xcode_build_settings_path) do |line|
    matches = line.match(/FLUTTER_ROOT\\=(.*)/)
    return matches[1].strip if matches
  end
  raise "FLUTTER_ROOT not found in #{generated_xcode_build_settings_path}. Try deleting Generated.xcconfig, then run flutter pub get"
end

require File.expand_path(File.join('packages', 'flutter_tools', 'bin', 'podhelper'), flutter_root)

flutter_ios_podfile_setup

target 'Runner' do
  use_frameworks!
  use_modular_headers!

  flutter_install_all_ios_pods File.dirname(File.realpath(__FILE__))
end

post_install do |installer|
  installer.pods_project.targets.each do |target|
    flutter_additional_ios_build_settings(target)
  end
end
'''


def get_ios_launch_screen() -> str:
    """Generate iOS LaunchScreen.storyboard."""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.Storyboard.XIB" version="3.0" toolsVersion="21701" targetRuntime="iOS.CocoaTouch" propertyAccessControl="none" useAutolayout="YES" launchScreen="YES" useTraitCollections="YES" useSafeAreas="YES" colorMatched="YES" initialViewController="01J-lp-oVM">
    <device id="retina6_12" orientation="portrait" appearance="light"/>
    <dependencies>
        <plugIn identifier="com.apple.InterfaceBuilder.IBCocoaTouchPlugin" version="21678"/>
        <capability name="Safe area layout guides" minToolsVersion="9.0"/>
        <capability name="documents saved in the Xcode 8 format" minToolsVersion="8.0"/>
    </dependencies>
    <scenes>
        <!--View Controller-->
        <scene sceneID="EHf-IW-A2E">
            <objects>
                <viewController id="01J-lp-oVM" sceneMemberID="viewController">
                    <view key="view" contentMode="scaleToFill" id="Ze5-6b-2t3">
                        <rect key="frame" x="0.0" y="0.0" width="393" height="852"/>
                        <autoresizingMask key="autoresizingMask" widthSizable="YES" heightSizable="YES"/>
                        <color key="backgroundColor" red="1" green="1" blue="1" alpha="1" colorSpace="custom" customColorSpace="sRGB"/>
                        <viewLayoutGuide key="safeArea" id="Bcu-3y-fUS"/>
                    </view>
                </viewController>
                <placeholder placeholderIdentifier="IBFirstResponder" id="iYj-Kq-Ea1" userLabel="First Responder" sceneMemberID="firstResponder"/>
            </objects>
            <point key="canvasLocation" x="52.671755725190835" y="375"/>
        </scene>
    </scenes>
</document>
'''


def get_ios_main_storyboard() -> str:
    """Generate iOS Main.storyboard."""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.Storyboard.XIB" version="3.0" toolsVersion="21701" targetRuntime="iOS.CocoaTouch" propertyAccessControl="none" useAutolayout="YES" useTraitCollections="YES" useSafeAreas="YES" colorMatched="YES" initialViewController="BYZ-38-t0r">
    <device id="retina6_12" orientation="portrait" appearance="light"/>
    <dependencies>
        <plugIn identifier="com.apple.InterfaceBuilder.IBCocoaTouchPlugin" version="21678"/>
        <capability name="Safe area layout guides" minToolsVersion="9.0"/>
        <capability name="documents saved in the Xcode 8 format" minToolsVersion="8.0"/>
    </dependencies>
    <scenes>
        <!--Flutter View Controller-->
        <scene sceneID="tne-QT-ifu">
            <objects>
                <viewController id="BYZ-38-t0r" customClass="FlutterViewController" sceneMemberID="viewController">
                    <view key="view" contentMode="scaleToFill" id="8bC-Xf-vdC">
                        <rect key="frame" x="0.0" y="0.0" width="393" height="852"/>
                        <autoresizingMask key="autoresizingMask" widthSizable="YES" heightSizable="YES"/>
                        <color key="backgroundColor" white="1" alpha="1" colorSpace="custom" customColorSpace="genericGamma22GrayColorSpace"/>
                        <viewLayoutGuide key="safeArea" id="6Tk-OE-BBY"/>
                    </view>
                </viewController>
                <placeholder placeholderIdentifier="IBFirstResponder" id="dkx-z0-nzr" sceneMemberID="firstResponder"/>
            </objects>
            <point key="canvasLocation" x="52" y="375"/>
        </scene>
    </scenes>
</document>
'''


def get_widget_test(app_name: str) -> str:
    """Generate basic widget test."""
    snake_name = app_name.lower().replace(" ", "_").replace("-", "_")
    return f'''import 'package:flutter_test/flutter_test.dart';

void main() {{
  testWidgets('App renders correctly', (WidgetTester tester) async {{
    // TODO: Import your App widget and test it
    // await tester.pumpWidget(const MyApp());
    // expect(find.text('Hello'), findsOneWidget);
    expect(true, isTrue);
  }});
}}
'''


def get_gitignore() -> str:
    """Generate .gitignore."""
    return '''# Miscellaneous
*.class
*.log
*.pyc
*.swp
.DS_Store
.atom/
.buildlog/
.history
.svn/
migrate_working_dir/

# IntelliJ related
*.iml
*.ipr
*.iws
.idea/

# VS Code
.vscode/

# Flutter/Dart/Pub related
**/doc/api/
**/ios/Flutter/.last_build_id
.dart_tool/
.flutter-plugins
.flutter-plugins-dependencies
.pub-cache/
.pub/
/build/

# Symbolication related
app.*.symbols

# Obfuscation related
app.*.map.json

# Android Studio
/android/app/debug
/android/app/profile
/android/app/release

# iOS
/ios/Pods/
/ios/.symlinks/
/ios/Flutter/Flutter.framework
/ios/Flutter/Flutter.podspec
'''


def generate_scaffold_files(app_name: str, spec: dict[str, Any]) -> list[dict[str, str]]:
    """Generate all scaffold files for a Flutter project.

    Args:
        app_name: Name of the app
        spec: Full app specification

    Returns:
        List of {"path": "...", "content": "..."} dictionaries
    """
    description = spec.get("description", f"{app_name} - A Flutter application")
    snake_name = app_name.lower().replace(" ", "_").replace("-", "_")

    files = [
        # Root files
        {"path": "pubspec.yaml", "content": get_pubspec_yaml(app_name, description)},
        {"path": "analysis_options.yaml", "content": get_analysis_options()},
        {"path": ".gitignore", "content": get_gitignore()},

        # Android files
        {"path": "android/app/build.gradle", "content": get_android_build_gradle(app_name)},
        {"path": "android/app/src/main/AndroidManifest.xml", "content": get_android_manifest(app_name)},
        {"path": f"android/app/src/main/kotlin/com/example/{snake_name}/MainActivity.kt",
         "content": get_main_activity_kt(app_name)},
        {"path": "android/app/src/main/res/values/styles.xml", "content": get_android_styles_xml()},
        {"path": "android/app/src/main/res/values-night/styles.xml", "content": get_android_styles_night_xml()},
        {"path": "android/app/src/main/res/drawable/launch_background.xml",
         "content": get_android_launch_background()},
        {"path": "android/app/src/main/res/drawable-v21/launch_background.xml",
         "content": get_android_launch_background()},
        {"path": "android/build.gradle", "content": get_android_root_build_gradle()},
        {"path": "android/settings.gradle", "content": get_android_settings_gradle(app_name)},
        {"path": "android/gradle/wrapper/gradle-wrapper.properties", "content": get_android_gradle_wrapper()},

        # iOS files
        {"path": "ios/Runner/AppDelegate.swift", "content": get_ios_app_delegate()},
        {"path": "ios/Runner/Info.plist", "content": get_ios_info_plist(app_name)},
        {"path": "ios/Podfile", "content": get_ios_podfile()},
        {"path": "ios/Runner/Base.lproj/LaunchScreen.storyboard",
         "content": get_ios_launch_screen()},
        {"path": "ios/Runner/Base.lproj/Main.storyboard",
         "content": get_ios_main_storyboard()},

        # Web files
        {"path": "web/index.html", "content": get_web_index_html(app_name)},
        {"path": "web/manifest.json", "content": get_web_manifest(app_name)},

        # Asset directories (empty placeholders)
        {"path": "assets/images/.gitkeep", "content": ""},
        {"path": "assets/icons/.gitkeep", "content": ""},

        # Test directory placeholder
        {"path": "test/widget_test.dart", "content": get_widget_test(app_name)},
    ]

    return files
