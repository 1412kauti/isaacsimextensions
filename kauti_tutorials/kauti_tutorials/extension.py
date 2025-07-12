import omni.ext
import omni.ui as ui
import omni.kit.commands
import omni.usd
import carb
import os
from omni.kit.window.file_importer import get_file_importer
from pxr import Gf, UsdGeom

class SimpleUSSDZLoaderExtension(omni.ext.IExt):
    def on_startup(self, ext_id):
        carb.log_info("[USDZ Loader] Extension starting up")
        
        self._window = None
        self._selected_file_path = ""
        self._current_prim = None
        self._current_xform = None
        
        self._build_ui()
        
    def _build_ui(self):
        self._window = ui.Window("📦 Simple USDZ Loader", width=400, height=500)
        
        with self._window.frame:
            with ui.VStack(spacing=10):
                # Title
                ui.Label("USDZ File Loader", 
                        style={"font_size": 18, "color": 0xFF00AAFF})
                
                ui.Separator(height=5)
                
                # File Loading Section
                with ui.CollapsableFrame("📁 File Loading", height=0, collapsed=False):
                    with ui.VStack(spacing=5):
                        ui.Label("Selected File:")
                        self._file_path_label = ui.Label("No file selected", 
                                                       style={"color": 0xFFFFAA00})
                        
                        # Browse button
                        ui.Button("Browse for USDZ File", 
                                 clicked_fn=self._browse_for_file,
                                 height=40)
                        
                        # Load button
                        ui.Button("Load as 'Name1'", 
                                 clicked_fn=self._load_usdz_file,
                                 height=40,
                                 style={"color": 0xFF00FF00})
                
                # Position Controls
                with ui.CollapsableFrame("📍 Position Controls", height=0, collapsed=False):
                    with ui.VStack(spacing=5):
                        # X Position
                        with ui.HStack():
                            ui.Label("X:", width=30)
                            self._pos_x_slider = ui.FloatDrag(min=-100.0, max=100.0, step=0.1)
                            self._pos_x_slider.model.set_value(0.0)
                            self._pos_x_slider.model.add_value_changed_fn(self._on_position_changed)
                        
                        # Y Position  
                        with ui.HStack():
                            ui.Label("Y:", width=30)
                            self._pos_y_slider = ui.FloatDrag(min=-100.0, max=100.0, step=0.1)
                            self._pos_y_slider.model.set_value(0.0)
                            self._pos_y_slider.model.add_value_changed_fn(self._on_position_changed)
                        
                        # Z Position
                        with ui.HStack():
                            ui.Label("Z:", width=30)
                            self._pos_z_slider = ui.FloatDrag(min=-100.0, max=100.0, step=0.1)
                            self._pos_z_slider.model.set_value(0.0)
                            self._pos_z_slider.model.add_value_changed_fn(self._on_position_changed)
                        
                        # Reset Position button
                        ui.Button("Reset Position", 
                                 clicked_fn=self._reset_position,
                                 height=30)
                
                # Rotation Controls
                with ui.CollapsableFrame("🔄 Rotation Controls", height=0, collapsed=False):
                    with ui.VStack(spacing=5):
                        # X Rotation (Roll)
                        with ui.HStack():
                            ui.Label("Roll (X):", width=60)
                            self._rot_x_slider = ui.FloatDrag(min=-180.0, max=180.0, step=1.0)
                            self._rot_x_slider.model.set_value(0.0)
                            self._rot_x_slider.model.add_value_changed_fn(self._on_rotation_changed)
                        
                        # Y Rotation (Pitch)
                        with ui.HStack():
                            ui.Label("Pitch (Y):", width=60)
                            self._rot_y_slider = ui.FloatDrag(min=-180.0, max=180.0, step=1.0)
                            self._rot_y_slider.model.set_value(0.0)
                            self._rot_y_slider.model.add_value_changed_fn(self._on_rotation_changed)
                        
                        # Z Rotation (Yaw)
                        with ui.HStack():
                            ui.Label("Yaw (Z):", width=60)
                            self._rot_z_slider = ui.FloatDrag(min=-180.0, max=180.0, step=1.0)
                            self._rot_z_slider.model.set_value(0.0)
                            self._rot_z_slider.model.add_value_changed_fn(self._on_rotation_changed)
                        
                        # Reset Rotation button
                        ui.Button("Reset Rotation", 
                                 clicked_fn=self._reset_rotation,
                                 height=30)
                
                # Status
                self._status_label = ui.Label("Ready to load file", 
                                            style={"color": 0xFFFFFFFF})
    
    def _browse_for_file(self):
        """Open file browser to select USDZ file"""
        try:
            # Get the file importer
            file_importer = get_file_importer()
            
            # Define file filters for USDZ files
            file_importer.show_window(
                title="Select USDZ File",
                import_button_label="Select",
                import_handler=self._on_file_selected,
                file_extension_types=[
                    (".usdz", "USDZ Files"),
                    (".usd", "USD Files"),
                    (".*", "All Files")
                ]
            )
            
        except Exception as e:
            carb.log_error(f"Error opening file browser: {str(e)}")
            self._status_label.text = f"Error: {str(e)}"
            self._status_label.style = {"color": 0xFFFF0000}
    
    def _on_file_selected(self, filename: str, dirname: str, selections):
        """Callback when file is selected from browser"""
        try:
            if filename and dirname:
                self._selected_file_path = os.path.join(dirname, filename)
                
                # Update UI
                self._file_path_label.text = os.path.basename(self._selected_file_path)
                self._file_path_label.style = {"color": 0xFF00FF00}
                
                self._status_label.text = f"File selected: {filename}"
                self._status_label.style = {"color": 0xFF00FF00}
                
                carb.log_info(f"[USDZ Loader] Selected file: {self._selected_file_path}")
            
        except Exception as e:
            carb.log_error(f"Error handling file selection: {str(e)}")
            self._status_label.text = f"Selection error: {str(e)}"
            self._status_label.style = {"color": 0xFFFF0000}
    
    def _load_usdz_file(self):
        """Load the selected USDZ file onto the stage as 'Name1'"""
        if not self._selected_file_path:
            self._status_label.text = "Please select a file first"
            self._status_label.style = {"color": 0xFFFFAA00}
            return
        
        try:
            # Get the current stage
            stage = omni.usd.get_context().get_stage()
            if not stage:
                self._status_label.text = "Error: No stage found"
                self._status_label.style = {"color": 0xFFFF0000}
                return
            
            # Define the prim path
            prim_path = "/World/Name1"
            
            # Create World if it doesn't exist
            world_path = "/World"
            if not stage.GetPrimAtPath(world_path):
                omni.kit.commands.execute(
                    "CreatePrimCommand",
                    prim_type="Xform",
                    prim_path=world_path
                )
            
            # Delete existing Name1 if it exists
            if stage.GetPrimAtPath(prim_path):
                omni.kit.commands.execute("DeletePrimsCommand", paths=[prim_path])
            
            # Load the USDZ file as a reference
            omni.kit.commands.execute(
                "CreateReference",
                usd_context=omni.usd.get_context(),
                path_to=prim_path,
                asset_path=self._selected_file_path,
                instanceable=False
            )
            
            # Success!
            self._status_label.text = f"✅ Loaded {os.path.basename(self._selected_file_path)} as 'Name1'"
            self._status_label.style = {"color": 0xFF00FF00}
            
            # Cache the prim reference
            self._current_prim = stage.GetPrimAtPath(prim_path)
            if self._current_prim and self._current_prim.IsValid():
                self._current_xform = UsdGeom.Xformable(self._current_prim)
                # Set initial transform
                self._update_transform()
            
            carb.log_info(f"[USDZ Loader] Successfully loaded {self._selected_file_path} as {prim_path}")
            
        except Exception as e:
            carb.log_error(f"[USDZ Loader] Error loading file: {str(e)}")
            self._status_label.text = f"❌ Error: {str(e)}"
            self._status_label.style = {"color": 0xFFFF0000}
    
    def _update_transform(self):
        """Update the transform of the loaded object"""
        if not self._current_xform:
            return
        
        try:
            # Get current values from sliders
            pos_x = self._pos_x_slider.model.get_value_as_float()
            pos_y = self._pos_y_slider.model.get_value_as_float()
            pos_z = self._pos_z_slider.model.get_value_as_float()
            
            rot_x = self._rot_x_slider.model.get_value_as_float()
            rot_y = self._rot_y_slider.model.get_value_as_float()
            rot_z = self._rot_z_slider.model.get_value_as_float()
            
            # Clear existing transform ops and create new ones
            self._current_xform.ClearXformOpOrder()
            
            # Add translate operation
            translate_op = self._current_xform.AddTranslateOp()
            translate_op.Set(Gf.Vec3d(pos_x, pos_y, pos_z))
            
            # Add rotation operation (XYZ euler)
            rotate_op = self._current_xform.AddRotateXYZOp()
            rotate_op.Set(Gf.Vec3f(rot_x, rot_y, rot_z))
            
        except Exception as e:
            carb.log_error(f"Error updating transform: {str(e)}")
    
    def _on_position_changed(self, model):
        """Called when position sliders change"""
        self._update_transform()
    
    def _on_rotation_changed(self, model):
        """Called when rotation sliders change"""
        self._update_transform()
    
    def _reset_position(self):
        """Reset position to origin"""
        self._pos_x_slider.model.set_value(0.0)
        self._pos_y_slider.model.set_value(0.0)
        self._pos_z_slider.model.set_value(0.0)
        self._update_transform()
    
    def _reset_rotation(self):
        """Reset rotation to zero"""
        self._rot_x_slider.model.set_value(0.0)
        self._rot_y_slider.model.set_value(0.0)
        self._rot_z_slider.model.set_value(0.0)
        self._update_transform()
    
    def on_shutdown(self):
        carb.log_info("[USDZ Loader] Extension shutting down")
        if self._window:
            self._window.destroy()
            self._window = None