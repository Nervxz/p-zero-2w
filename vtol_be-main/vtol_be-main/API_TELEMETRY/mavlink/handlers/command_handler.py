"""
Command Handler for MAVLink API  
Handles MAVLink command sending (arm/disarm, flight modes, etc.)
"""

import logging
from typing import Optional
from pymavlink import mavutil
from pymavlink.dialects.v20 import common as mavlink

logger = logging.getLogger(__name__)

class CommandHandler:
    """Handler for MAVLink command operations"""
    
    def __init__(self, connection: mavutil.mavlink_connection):
        self.connection = connection
    
    def send_command_long(self, command: int, param1: float = 0, param2: float = 0, 
                         param3: float = 0, param4: float = 0, param5: float = 0, 
                         param6: float = 0, param7: float = 0, confirmation: int = 0) -> bool:
        """
        Send COMMAND_LONG message
        
        Args:
            command: MAV_CMD_* command ID
            param1-param7: Command parameters
            confirmation: Command confirmation counter
            
        Returns:
            bool: True if sent successfully
        """
        try:
            self.connection.mav.command_long_send(
                target_system=self.connection.target_system,
                target_component=self.connection.target_component,
                command=command,
                confirmation=confirmation,
                param1=param1,
                param2=param2,
                param3=param3,
                param4=param4,
                param5=param5,
                param6=param6,
                param7=param7
            )
            logger.debug(f"Sent command {command}")
            return True
        except Exception as e:
            logger.error(f"Failed to send command {command}: {e}")
            return False
    
    def send_arm_command(self, arm: bool, force: bool = False) -> bool:
        """
        Send arm/disarm command
        
        Args:
            arm: True to arm, False to disarm
            force: Force arming (bypass safety checks)
            
        Returns:
            bool: True if sent successfully
        """
        param1 = 1.0 if arm else 0.0
        param2 = 21196.0 if force else 0.0  # Force arming magic number
        
        return self.send_command_long(
            mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
            param1=param1,
            param2=param2
        )
    
    def set_flight_mode(self, mode: int, custom_mode: Optional[int] = None) -> bool:
        """
        Set flight mode using SET_MODE
        
        Args:
            mode: Base mode (MAV_MODE_FLAG_*)
            custom_mode: Custom mode (autopilot-specific)
            
        Returns:
            bool: True if sent successfully
        """
        try:
            # For ArduPilot, use custom mode directly
            if custom_mode is not None:
                base_mode = mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED
                self.connection.mav.set_mode_send(
                    target_system=self.connection.target_system,
                    base_mode=base_mode,
                    custom_mode=custom_mode
                )
            else:
                self.connection.mav.set_mode_send(
                    target_system=self.connection.target_system,
                    base_mode=mode,
                    custom_mode=0
                )
            
            logger.debug(f"Set flight mode: base={mode}, custom={custom_mode}")
            return True
        except Exception as e:
            logger.error(f"Failed to set flight mode: {e}")
            return False
    
    def set_ardupilot_mode(self, mode_number: int) -> bool:
        """
        Set ArduPilot flight mode by mode number
        
        Args:
            mode_number: ArduPilot mode number (0=MANUAL, 2=STABILIZE, etc.)
            
        Returns:
            bool: True if sent successfully
        """
        return self.set_flight_mode(
            mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED, 
            mode_number
        )
    
    def takeoff(self, altitude: float, pitch: float = 0.0, yaw: float = 0.0) -> bool:
        """
        Command takeoff
        
        Args:
            altitude: Target altitude (meters)
            pitch: Minimum pitch angle (degrees, 0=default)
            yaw: Yaw angle (degrees, NaN=current yaw)
            
        Returns:
            bool: True if sent successfully
        """
        return self.send_command_long(
            mavlink.MAV_CMD_NAV_TAKEOFF,
            param1=pitch,
            param4=yaw,
            param7=altitude
        )
    
    def land(self, abort_alt: float = 0.0, precision_land_mode: int = 0, 
             yaw: float = float('nan'), lat: float = 0.0, lon: float = 0.0, 
             alt: float = 0.0) -> bool:
        """
        Command land
        
        Args:
            abort_alt: Abort altitude (meters)
            precision_land_mode: Precision landing mode
            yaw: Landing yaw angle (degrees)
            lat: Target latitude (degrees, 0=current position)
            lon: Target longitude (degrees, 0=current position)  
            alt: Target altitude (meters, 0=ground level)
            
        Returns:
            bool: True if sent successfully
        """
        return self.send_command_long(
            mavlink.MAV_CMD_NAV_LAND,
            param1=abort_alt,
            param2=precision_land_mode,
            param4=yaw,
            param5=lat,
            param6=lon,
            param7=alt
        )
    
    def return_to_launch(self) -> bool:
        """
        Command return to launch (RTL)
        
        Returns:
            bool: True if sent successfully
        """
        return self.send_command_long(mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH)
    
    def goto_position(self, lat: float, lon: float, alt: float, 
                     hold_time: float = 0.0, accept_radius: float = 0.0,
                     pass_radius: float = 0.0, yaw: float = float('nan')) -> bool:
        """
        Go to specific position
        
        Args:
            lat: Target latitude (degrees)
            lon: Target longitude (degrees)
            alt: Target altitude (meters)
            hold_time: Hold time at waypoint (seconds)
            accept_radius: Acceptance radius (meters)
            pass_radius: Pass-through radius (meters)
            yaw: Target yaw angle (degrees, NaN=no change)
            
        Returns:
            bool: True if sent successfully
        """
        return self.send_command_long(
            mavlink.MAV_CMD_NAV_WAYPOINT,
            param1=hold_time,
            param2=accept_radius,
            param3=pass_radius,
            param4=yaw,
            param5=lat,
            param6=lon,
            param7=alt
        )
    
    def set_servo(self, servo_number: int, pwm_value: int) -> bool:
        """
        Set servo PWM value
        
        Args:
            servo_number: Servo number (1-8)
            pwm_value: PWM value (typically 1000-2000)
            
        Returns:
            bool: True if sent successfully
        """
        return self.send_command_long(
            mavlink.MAV_CMD_DO_SET_SERVO,
            param1=servo_number,
            param2=pwm_value
        )
    
    def set_camera_trigger(self, trigger_cycle: float = 0.0, shutter_int: float = 0.0,
                          trigger_pin: int = 0, session_ctrl: int = 0, zoom_pos: float = 0.0,
                          zoom_step: float = 0.0, focus_lock: int = 0) -> bool:
        """
        Trigger camera shutter
        
        Args:
            trigger_cycle: Trigger cycle time (seconds, 0=single shot)
            shutter_int: Shutter integration time (milliseconds)
            trigger_pin: Trigger pin number
            session_ctrl: Session control (0=disable, 1=enable)
            zoom_pos: Zoom position
            zoom_step: Zoom step
            focus_lock: Focus lock (0=unlock, 1=lock)
            
        Returns:
            bool: True if sent successfully
        """
        return self.send_command_long(
            mavlink.MAV_CMD_DO_DIGICAM_CONTROL,
            param1=session_ctrl,
            param2=zoom_pos,
            param3=zoom_step,
            param4=focus_lock,
            param5=trigger_pin,
            param6=shutter_int,
            param7=trigger_cycle
        )
    
    def reboot_autopilot(self, onboard_computer: bool = False) -> bool:
        """
        Reboot autopilot
        
        Args:
            onboard_computer: Also reboot onboard computer
            
        Returns:
            bool: True if sent successfully
        """
        param1 = 1.0  # Reboot autopilot
        param2 = 1.0 if onboard_computer else 0.0  # Reboot onboard computer
        
        return self.send_command_long(
            mavlink.MAV_CMD_PREFLIGHT_REBOOT_SHUTDOWN,
            param1=param1,
            param2=param2
        )
