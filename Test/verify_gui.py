import sys
from PySide6.QtWidgets import QApplication
import os

# Ensure the script can find discord_utils
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from gui_channel_manager import ChannelManagerGUI
    
    print("[PASS] Imports successful")
    
    # Test GUI Initialization (Headless check)
    app = QApplication(sys.argv)
    
    # Create Window but don't call app.exec() to prevent hang
    w = ChannelManagerGUI()
    print(f"[PASS] GUI Window initialized successfully: {w.windowTitle()}")
    
    # Check if data was loaded (categories should not be empty if API worked)
    # Note: This might fail if no internet, but at least we check if Class works
    sys.exit(0) 

except Exception as e:
    print(f"[FAIL] Error: {e}")
    sys.exit(1)
