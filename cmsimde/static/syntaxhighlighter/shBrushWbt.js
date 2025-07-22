// SyntaxHighlighter brush for Webots
;(function()
{
    typeof(require) != 'undefined' ? SyntaxHighlighter = require('shCore').SyntaxHighlighter : null;
    
    function Brush()
    {
        // Webots node types
        var nodes = 'WorldInfo Viewpoint Background DirectionalLight PointLight SpotLight Group ' +
                   'Transform Shape Material Appearance PBRAppearance ImageTexture TextureTransform '+
                   'Robot Solid Accelerometer Brake Camera Compass Connector Display ' +
                   'DistanceSensor Emitter GPS Gyro InertialUnit LED LightSensor LinearMotor ' +
                   'Motor Pen Position2D PositionSensor Propeller Radar RangeFinder Receiver' + 
                   'Speaker TouchSensor Track VacuumGripper Physics BoundingObject Box Capsule ' +
                   'Cylinder ElevationGrid IndexedFaceSet Plane Sphere HingeJoint Hinge2Joint BallJoint ' +
                   'SliderJoint Normal Color Coordinate Fog Focus LensFlare Lidar Muscle ' + 
                   'Charger CadShape ConveyorBelt Skin ContactProperties Damping FocalPoint ' +
                   'Field MetalAxis MetalParts ParabolicReflector ParaboloidMesh Altimeter ' +
                   'Microphone';

        // Webots controller API functions
        var functions = 'wb_robot_init wb_robot_step wb_robot_cleanup ' +
                       'wb_motor_set_position wb_motor_set_velocity wb_motor_get_position ' +
                       'wb_distance_sensor_enable wb_distance_sensor_get_value ' +
                       'wb_camera_enable wb_camera_get_image wb_camera_get_width wb_camera_get_height ' +
                       'wb_led_set wb_receiver_enable wb_receiver_get_data ' +
                       'wb_emitter_send wb_supervisor_field_get_sf_vec3f ' +
                       'wb_supervisor_node_get_field wb_supervisor_field_get_sf_rotation ' +
                       'wb_robot_get_time wb_robot_battery_sensor_enable ' +
                       'wb_compass_enable wb_compass_get_values ' +
                       'wb_gps_enable wb_gps_get_values ' +
                       'wb_gyro_enable wb_gyro_get_values ' +
                       'wb_inertial_unit_enable wb_inertial_unit_get_roll_pitch_yaw ' +
                       'wb_keyboard_enable wb_keyboard_get_key ' +
                       'wb_lidar_enable wb_lidar_get_range_image ' +
                       'wb_motor_set_torque wb_position_sensor_enable ' +
                       'wb_touch_sensor_enable wb_touch_sensor_get_value';

        // Constants and fields
        var constants = 'TRUE FALSE NULL TIME_STEP WB_STDOUT WB_STDERR ' +
                       'SIMULATION_MODE_PAUSE SIMULATION_MODE_REAL_TIME SIMULATION_MODE_RUN ' +
                       'WB_ANGULAR WB_LINEAR WB_KEYBOARD_KEY WB_KEYBOARD_END ' +
                       'WB_MOTOR_ROTATIONAL WB_MOTOR_LINEAR ' +
                       'WB_DISTANCE_SENSOR_GENERIC WB_DISTANCE_SENSOR_INFRA_RED WB_DISTANCE_SENSOR_SONAR ' +
                       'WB_GPS_LOCAL_COORDINATE WB_GPS_WGS84_COORDINATE ' +
                       'WB_LED_ON WB_LED_OFF';

        // Data types
        var datatypes = 'void int double float char bool WbDeviceTag WbFieldType ' +
                       'WbNodeType WbRobotMode const static typedef struct';

        // Keywords
        var keywords = 'include define if else while for do break continue return switch case default ' +
                      'extern sizeof';

        this.regexList = [
            // Comments
            { regex: /\/\*[\s\S]*?\*\//gm,                     css: 'comments' },     // Multi-line comments
            { regex: /\/\/.*$/gm,                              css: 'comments' },     // Single line comments
            
            // Strings
            { regex: /"(?:\\.|[^"\\])*"/g,                     css: 'string' },       // Double quoted strings
            
            // Numbers
            { regex: /\b-?(?:\d*\.?\d+|\d+\.?\d*)\b/g,        css: 'number' },       // Numbers
            
            // Preprocessor directives
            { regex: /#\w+/gm,                                 css: 'preprocessor' },
            
            // Functions
            { regex: new RegExp(this.getKeywords(functions), 'gm'),  css: 'functions' },
            
            // Node types
            { regex: new RegExp(this.getKeywords(nodes), 'gm'),      css: 'color2' },
            
            // Constants
            { regex: new RegExp(this.getKeywords(constants), 'gm'),   css: 'constants' },
            
            // Data types
            { regex: new RegExp(this.getKeywords(datatypes), 'gm'),   css: 'color1' },
            
            // Keywords
            { regex: new RegExp(this.getKeywords(keywords), 'gm'),    css: 'keyword' }
        ];
    }

    Brush.prototype = new SyntaxHighlighter.Highlighter();
    Brush.aliases = ['webots', 'wbt'];

    SyntaxHighlighter.brushes.Webots = Brush;

    // CommonJS
    typeof(exports) != 'undefined' ? exports.Brush = Brush : null;
})();