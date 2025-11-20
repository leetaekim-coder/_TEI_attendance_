import customtkinter as ctk
from tkinter import messagebox, filedialog 
import re 
import os 
from datetime import datetime, date
from exchange_rate_viewer import ExchangeRateViewer # ⭐ ADDED: This line is added ⭐

# ⭐ ADDED: Regular expression check for HH:MM format (00:00 ~ 23:59) ⭐
TIME_REGEX = re.compile(r'^(0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$')

class SettingsViewCTK(ctk.CTkFrame):
    """
    A view that provides settings for the attendance standard time, employee list, and PDF export functionality.
    (Holiday list functionality removed)
    """
    # ⭐ MODIFIED: Added theme_callback argument. ⭐
    def __init__(self, master, data_manager, save_callback, statistics_exporter, theme_callback):

# ⭐ Moved font definition inside __init__ (Fix RuntimeError) ⭐
        self.MANUAL_FONT = ctk.CTkFont(family="Malgun Gothic", size=10)
        # TEXT_AREA_FONT is a tuple, so it can be defined at the class level, but for consistency, defining it as self. here is also fine.
        # Original: TEXT_AREA_FONT = ("Malgun Gothic", 10)
        self.TEXT_AREA_FONT_CTK = ctk.CTkFont(family="Malgun Gothic", size=18)
        self.EMPLOYEE_TEXTBOX_FONT = ctk.CTkFont(family="Malgun Gothic", size=14)

        super().__init__(master, corner_radius=10)
        self.data_manager = data_manager
        self.save_callback = save_callback

        self.statistics_exporter = statistics_exporter # Store PDF export object
        self.theme_callback = theme_callback # New: Store theme change callback

        print(f"[DEBUG] SettingsViewCTK init - statistics_exporter type: {type(self.statistics_exporter)}")
        
        # 2-column layout settings
        self.grid_columnconfigure(0, weight=0) # Left Panel (Time/Buttons) fixed
        self.grid_columnconfigure(1, weight=1) # Right Panel (Text Area) expands
        self.grid_rowconfigure(0, weight=1)    # Full height expands

        self._build_ui()
        self.refresh_view() # Load initial settings

# ... (Inside SettingsViewCTK Class)

    def _apply_settings(self):
        """
        Method called when the Save Settings button is clicked.
        (Method name may vary depending on the actual code.)
        """
        
        # 1. Validate and save Standard Attendance Time
        # Assume self.standard_time_entry is the standard time input widget
        time_input = self.standard_time_entry.get().strip() 
        
        # Regex to check for HH:MM format (e.g., 09:00)
        time_pattern = r"^\d{2}:\d{2}$"
        
        # ⭐ Core fix for error: Check if input matches format, otherwise stop saving ⭐
        if not re.match(time_pattern, time_input):
            messagebox.showerror("Error", "Invalid time format. Please enter in HH:MM format (e.g., 09:00).")
            return # Stop saving process on validation failure
            
        # If validation passes, save standard time
        self.data_manager.settings['attendance_time'] = time_input
        
        # 2. Parse and save employee list (Maintain existing logic)
        employee_list_text = self.employee_textbox.get("1.0", "end-1c")
        employees = [name.strip() for name in employee_list_text.split('\n') if name.strip()]
        self.data_manager.settings['employees'] = employees
        
        # 3. Save data
        self.save_callback()
        
        messagebox.showinfo("Complete", "Settings and employee list successfully saved.")
        self.refresh_view()


    def _build_ui(self):
        
        # ----------------------------------------------------
        # 1. Left Panel (Time Settings, Buttons) - Column 0
        # ----------------------------------------------------
        left_panel = ctk.CTkFrame(self, fg_color="transparent")
        left_panel.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        left_panel.grid_columnconfigure(0, weight=1)
        left_panel.grid_columnconfigure(1, weight=1)

        # 1. Standard Check-in Time Setting
        time_label = ctk.CTkLabel(left_panel, text="⏰ Standard Check-in Time (HH:MM)", font=ctk.CTkFont(size=14, weight="bold"))
        time_label.grid(row=0, column=0, columnspan=2, padx=5, pady=(0, 5), sticky="nw")

        self.attendance_time_entry = ctk.CTkEntry(left_panel, width=150, placeholder_text="09:00")
        self.attendance_time_entry.grid(row=1, column=0, columnspan=2, padx=5, pady=(0, 10), sticky="nw")
        
        # ⭐ [Request 2] Replace attendance time save button with integrated save button ⭐
        self.save_settings_button = ctk.CTkButton(
            left_panel, 
            text="✅ Save All Settings (Time/Employees) & Restart", 
            command=self._save_settings_handler, # Connect to new handler
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40
        )
        # Place integrated save button in row 2
        self.save_settings_button.grid(row=2, column=0, columnspan=2, pady=(20, 10), sticky="ew")

        # 2. PDF Export Button
        pdf_label = ctk.CTkLabel(left_panel, text="📋 Statistics Report", font=ctk.CTkFont(size=14, weight="bold"))
        pdf_label.grid(row=3, column=0, columnspan=2, padx=5, pady=(20, 5), sticky="nw")
        
        self.export_pdf_button = ctk.CTkButton(
            left_panel, 
            text="Export PDF Report", 
            command=self._export_pdf_handler,
            fg_color="#00BCD4", hover_color="#00ACC1"
        )
        self.export_pdf_button.grid(row=4, column=0, columnspan=2, padx=5, pady=(0, 10), sticky="ew")
        
        # 3. Open Backup Folder Button
        backup_label = ctk.CTkLabel(left_panel, text="📁 Backup and Data Management", font=ctk.CTkFont(size=14, weight="bold"))
        backup_label.grid(row=5, column=0, columnspan=2, padx=5, pady=(20, 5), sticky="nw")
        
        self.open_backup_button = ctk.CTkButton(
            left_panel, 
            text="Open Backup Folder", 
            command=self._open_backup_folder,
            fg_color="#607D8B", hover_color="#546E7A"
        )
        self.open_backup_button.grid(row=6, column=0, columnspan=2, padx=5, pady=(0, 10), sticky="ew")
        
        
        # ----------------------------------------------------
        # ⭐ 4. UI/Theme Settings (New Section) - Row 7 ⭐
        # ----------------------------------------------------
        theme_frame = ctk.CTkFrame(left_panel, corner_radius=10)
        theme_frame.grid(row=7, column=0, columnspan=2, padx=5, pady=(20, 10), sticky="ew")
        theme_frame.grid_columnconfigure(0, weight=1)
        theme_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            theme_frame, 
            text="✨ UI / Theme Settings", 
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="w")
        
        # 4.1. Appearance Mode
        ctk.CTkLabel(theme_frame, text="Appearance Mode:", anchor="w").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(
            theme_frame, 
            values=["Light", "Dark", "System"], 
            command=self._change_appearance_mode
        )
        self.appearance_mode_optionemenu.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        # 4.2. Color Theme
        ctk.CTkLabel(theme_frame, text="Color Theme:", anchor="w").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.color_theme_optionemenu = ctk.CTkOptionMenu(
            theme_frame, 
            values=["blue", "dark-blue", "green"], 
            command=self._change_color_theme
        )
        self.color_theme_optionemenu.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        
        # 4.3. Font Size (Slider)
        ctk.CTkLabel(theme_frame, text="Font Size (Requires Restart):", anchor="w").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.font_size_slider = ctk.CTkSlider(theme_frame, from_=8, to=14, number_of_steps=6)
        self.font_size_slider.set(11) # Set default value
        self.font_size_slider.grid(row=3, column=1, padx=10, pady=(5, 10), sticky="ew")
        self.font_size_slider.configure(state="disabled") # Disabled due to CTK constraints


        # ----------------------------------------------------
        # 5. Right Panel (Employee List) - Column 1
        # ----------------------------------------------------
        right_panel = ctk.CTkFrame(self, fg_color="transparent")
        # Sticky "new" is correct to prevent vertical expansion
        right_panel.grid(row=0, column=1, padx=10, pady=10, sticky="new") 
        right_panel.grid_rowconfigure(0, weight=0) # Label fixed
        right_panel.grid_rowconfigure(1, weight=1) # Text area expands
        right_panel.grid_columnconfigure(0, weight=1)

        # 6. Employee List 
        employees_label = ctk.CTkLabel(right_panel, text="🧑‍🤝‍🧑 Employee List (Enter one name per line)", font=ctk.CTkFont(size=14, weight="bold"))
        employees_label.grid(row=0, column=0, padx=5, pady=(0, 5), sticky="nw")

        self.employees_textbox = ctk.CTkTextbox(
            right_panel, 
            width=300, 
            wrap="word", 
            height=200,
            font=self.EMPLOYEE_TEXTBOX_FONT
        )

        # Sticky "new" is correct to prevent vertical expansion
        self.employees_textbox.grid(row=1, column=0, padx=5, pady=(0, 10), sticky="new")

# ⭐ New: 7. Added Exchange Rate Viewer ⭐
        # Added to row 2 of right_panel, Employee Textbox must be set to weight=1 in row 1.
        right_panel.grid_rowconfigure(2, weight=0) # New Exchange Rate Viewer fixed

        self.exchange_rate_viewer = ExchangeRateViewer(right_panel)
        self.exchange_rate_viewer.grid(row=2, column=0, padx=5, pady=(10, 10), sticky="ew") # Adjust width with "ew"
        
    def refresh_view(self):
        """Loads the saved settings values to the UI."""
        settings = self.data_manager.settings

        # 1. Load Standard Check-in Time (Existing)
        time_setting = settings.get('attendance_time', '09:00')
        self.attendance_time_entry.delete(0, 'end')
        self.attendance_time_entry.insert(0, time_setting)

        # 2. Load Employee List (Existing)
        employees = settings.get('employees', [])
        self.employees_textbox.delete("1.0", "end")
        self.employees_textbox.insert("1.0", '\n'.join(employees))

        # ⭐ New: Load Theme Settings ⭐
        # Note: These values should be loaded from self.data_manager.settings 
        # once the saving logic is implemented in the DataManager/GUIManager.
        current_mode = settings.get('appearance_mode', 'Dark')
        self.appearance_mode_optionemenu.set(current_mode)
        
        current_theme = settings.get('color_theme', 'green')
        self.color_theme_optionemenu.set(current_theme)

        font_size = settings.get('font_size', 11)
        self.font_size_slider.set(font_size)

    # ⭐ New: Callback methods for theme changes ⭐
    def _change_appearance_mode(self, new_mode: str):
        """Passes the Appearance Mode change request to the main app (GUIManagerCTK)."""
        if self.theme_callback:
            self.theme_callback(mode=new_mode)
        
    def _change_color_theme(self, new_theme: str):
        """Passes the Color Theme change request to the main app (GUIManagerCTK)."""
        if self.theme_callback:
            self.theme_callback(theme=new_theme)
            
# ⭐ Integrated Save Handler Implementation: Saves time and employees, handles restart prompt ⭐
    def _save_settings_handler(self):
        """
        Integrated save handler that saves both the standard check-in time and employee list, 
        and calls the callback after the restart prompt.
        """

        # 1. Validate and extract Standard Check-in Time
        new_time = self.attendance_time_entry.get().strip()

        # If input is empty, retrieve existing value from settings.json
        if not new_time:
            new_time = self.data_manager.settings.get('attendance_time')
            if not new_time:
                messagebox.showerror(
                    "Error",
                    "Standard attendance time is not set. Please enter in HH:MM format."
                )
                return

        # Check if the retrieved value is also in HH:MM format
        time_pattern = r"^(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$"
        if not re.match(time_pattern, new_time):
            messagebox.showerror(
                "Error",
                f"Invalid time format. Please enter in HH:MM format (e.g., 09:00). (Current value: {new_time})"
            )
            return # 👈 Stop saving and display error message here.

        # 2. Extract Employee List
        employee_text = self.employees_textbox.get("1.0", "end-1c") 
        normalized_text = employee_text.replace('\r\n', '\n').replace('\r', '\n').strip()
        new_employees = [e.strip() for e in normalized_text.split('\n') if e.strip()]

        # 3. Extract Theme Settings
        new_mode = self.appearance_mode_optionemenu.get()
        new_theme = self.color_theme_optionemenu.get()
        new_font_size = self.font_size_slider.get()

        # 4. Load existing holidays
        existing_holidays = self.data_manager.settings.get('holidays', [])

        # 5. Save settings
        try:
            # This function must be defined in data_manager_ctk.py.
            self.data_manager.save_settings(
                attendance_time=new_time,
                employees=new_employees,
                holidays=existing_holidays,
                appearance_mode=new_mode,
                color_theme=new_theme,
                font_size=new_font_size
            )
            all_saved_ok = True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")
            all_saved_ok = False

        # 6. Post-save actions
        if all_saved_ok:
            # Check if settings values changed and prompt for restart message
            # (When attendance_time or employees change)
            restart_needed = False 
            try:
                # Ideally, save_settings should be modified to return whether a change occurred, but
                # Display message box according to current logic.
                restart_needed = messagebox.askyesno(
                    "Settings Saved", 
                    "Standard check-in time or employee list has changed.\n\n"
                    "Would you like to restart the program immediately to apply the new settings?\n"
                    "(Attendance records will be recalculated based on the new standard time upon restart.)"
                )
                self.save_callback(restart_needed)

                if not restart_needed and self.statistics_exporter:
                    try:
                        self.statistics_exporter.refresh_view()
                    except Exception as refresh_e:
                        print(f"Statistics refresh error suppressed: {refresh_e}")

                    messagebox.showinfo(
                        "Save Complete", 
                        "Settings have been saved. You must manually restart the program for changes (employee list, recalculation) to take effect."
                    )
            except Exception as post_save_e:
                messagebox.showerror(
                    "Post-Save Warning", 
                    f"Settings were saved, but an error occurred during the restart process: {post_save_e}"
                )
                if 'restart_needed' in locals() and not restart_needed:
                    messagebox.showinfo(
                        "Save Complete", 
                        "Settings have been saved. You must manually restart the program for changes (employee list, recalculation) to take effect."
                    )



    def _export_pdf_handler(self):
        """Called when the PDF Export button is clicked. Uses the statistics_exporter object."""
        
        if not self.statistics_exporter:
            messagebox.showerror("Error", "PDF generation module is not initialized. Please restart the program.")
            return

        # 1. Select save path
        
        # Temporary: Set to export All Time statistics
        report_type = 'yearly' # Temporary: widest scope
        year = date.today().year
        month = None
        # Updated title and filename for English
        title = f"Attendance Statistics for {year}" 
        default_filename = f"Attendance_Report_{year}_Stats.pdf"
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=default_filename,
            title="Save PDF Report"
        )

        if not file_path:
            return # User canceled

        try:
            # ⭐ Core Fix: Call generate_pdf_summary method of StatisticsExporter object ⭐
            self.statistics_exporter.generate_pdf_summary(file_path, report_type, year, month) 
            messagebox.showinfo("Complete", f"PDF report successfully saved to:\n{file_path}")

        except Exception as e:
            # Display error message on PDF generation failure
            messagebox.showerror("Error", f"An error occurred during PDF export. Please check the functionality of the Statistics tab: {e}")
            
    def _open_backup_folder(self):
        """Opens the backup folder."""
        # Use defined string since DataManager.BACKUP_FOLDER is not directly accessible
        backup_path = "attendance_backups" 
        
        if not os.path.exists(backup_path):
            messagebox.showinfo("Info", f"Backup folder '{backup_path}' does not exist.")
            return

        try:
            # Open folder using OS-specific command
            os.startfile(backup_path) if os.name == 'nt' else os.system(f'xdg-open "{backup_path}"') 
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while opening the folder: {e}")