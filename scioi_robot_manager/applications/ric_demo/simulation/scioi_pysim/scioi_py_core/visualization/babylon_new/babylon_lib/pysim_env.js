var world_objects = {}


// =====================================================================================================================
class PysimScene extends Scene {
    constructor(id, config) {

        super(id);
        this.config = config
        console.log(config)
        this.createScene();
    }

    createScene() {
        // --- CAMERA ---
        this.camera = new BABYLON.ArcRotateCamera("Camera", 0, 0, 20, new BABYLON.Vector3(0,0.1,0), this.scene);
        this.camera.setPosition(new BABYLON.Vector3(0.02, 1.11, 2.3));
        this.camera.attachControl(this.canvas, true);
        this.camera.inputs.attached.keyboard.detachControl()
        this.camera.wheelPrecision = 100;
        this.camera.minZ = 0.1
        // --- LIGHTS ---
        this.light1 = new BABYLON.HemisphericLight("light", new BABYLON.Vector3(0.5,1,0), this.scene);
        this.light1.intensity = 1

        const gl = new BABYLON.GlowLayer("glow", this.scene);
        gl.intensity = 0

        // --- BACKGROUND ---
        this.defaultBackgroundColor = new BABYLON.Color3(1,1,1)
        this.scene.clearColor = this.defaultBackgroundColor;

        // --- Textbox ---
        this.ui = BABYLON.GUI.AdvancedDynamicTexture.CreateFullscreenUI("ui", true, this.scene);
        this.textbox_time = new BABYLON.GUI.TextBlock();
        this.textbox_time.fontSize = 20;
        this.textbox_time.text = "";
        this.textbox_time.color = "black";
        this.textbox_time.paddingTop = 3;
        this.textbox_time.paddingLeft = 3;
        this.textbox_time.textVerticalAlignment = BABYLON.GUI.Control.VERTICAL_ALIGNMENT_TOP;
        this.textbox_time.textHorizontalAlignment = BABYLON.GUI.Control.HORIZONTAL_ALIGNMENT_LEFT;
        this.ui.addControl(this.textbox_time);

        this.textbox_status = new BABYLON.GUI.TextBlock();
        this.textbox_status.fontSize = 40;
        this.textbox_status.text = "";
        this.textbox_status.color = "black";
        this.textbox_status.paddingTop = 3;
        this.textbox_status.paddingRight = 30;
        this.textbox_status.textVerticalAlignment = BABYLON.GUI.Control.VERTICAL_ALIGNMENT_TOP;
        this.textbox_status.textHorizontalAlignment = BABYLON.GUI.Control.HORIZONTAL_ALIGNMENT_RIGHT
        this.ui.addControl(this.textbox_status);


        this.textbox_title = new BABYLON.GUI.TextBlock();
        this.textbox_title.fontSize = 40;
        this.textbox_title.text = "Placeholder";
        this.textbox_title.color = "black";
        this.textbox_title.paddingTop = 3;
        this.textbox_title.paddingLeft = 3;
        this.textbox_title.textVerticalAlignment = BABYLON.GUI.Control.VERTICAL_ALIGNMENT_TOP;
        this.textbox_title.textHorizontalAlignment = BABYLON.GUI.Control.HORIZONTAL_ALIGNMENT_CENTER;
        this.ui.addControl(this.textbox_title);

        // --- Coordinate System ---
        drawCoordinateSystem(this.scene, length= 0.25)

        // --- GENERATION OF OBJECTS ---
        // this.buildWorld()

        // --- WEBAPP CONFIG ---
        // if ('webapp_config' in this.config && this.config['webapp_config'] != null){
        //     if ('title' in this.config['webapp_config']){
        //         this.textbox_title.text = this.config['webapp_config']['title']
        //     }
        //     if ('record' in this.config['webapp_config']){
        //         var recorder = new BABYLON.VideoRecorder(this.engine);
        //         recorder.startRecording(this.config['webapp_config']['record']['file'], this.config['webapp_config']['record']['time']);
        //     }
        //     if ('background' in this.config['webapp_config']){
        //         console.log(new BABYLON.Color3(this.config['webapp_config']['background'][0],this.config['webapp_config']['background'][1],this.config['webapp_config']['background'][2]))
        //         this.scene.clearColor = new BABYLON.Color3(this.config['webapp_config']['background'][0],this.config['webapp_config']['background'][1],this.config['webapp_config']['background'][2])
        //     }
        //
        // console.log("Finished")

        // object_id, object_type, object_config, visualization_config

         // world_objects['twipr1'] = new TWIPR_Robot(this.scene, 'twipr1', {'mesh': './models/twipr/twipr_generic', 'physics': {'wheel_diameter': 0.12}})
        let tg = new TiledGround(this.scene, 0.5, 10, 10, [0.5,0.5,0.5], [0.6,0.6,0.6])
        backend.sendMessage({'loaded': 1})
        return this.scene;
    }

    buildWorld() {
        // Check if the config has the appropriate entries:
        if (!("world" in this.config)){
            console.warn("No world definition in the config")
            return
        }
        if (!('objects' in this.config['world'])){
            console.warn("No world objects specified in the config")
            return
        }

        // Loop over the config and extract the objects
        for (const [key, value] of Object.entries(this.config['world']['objects'])){
            // Check if the object type is in the object config
            let babylon_object_name
            if (value.object_type in this.config['object_config']){
                babylon_object_name = this.config['object_config'][value.object_type]['BabylonObject']
                let objectPtr = eval(babylon_object_name)
                world_objects[key] = new objectPtr(this.scene, key, value.object_type, value, this.config['object_config'][value.object_type]['config'])

            } else {
                console.warn("Cannot find the object type in the object definition")
            }
        }
    }

    // -----------------------------------------------------------------------------------------------------------------


    // -----------------------------------------------------------------------------------------------------------------

    onSample(sample) {
        console.log("Got a sample")
        if ('type' in sample) {
            this.parseSample(sample['type'], sample['data'])
        }
    }
    // -----------------------------------------------------------------------------------------------------------------
    parseSample(command, data){
        switch (command){
            case 'addObject':
                this.addObject(data['id'],  data['class'], data['config'])
                break

            case 'removeObject':
                this.removeObject(data['id'])
                break

            case 'set':
                if (data['id'] === 'scene') {
                    break
                }
                else if (data['id'] in world_objects) {
                    world_objects[data['id']].set(data['parameter'], data['value'])
                }
                break
            case 'update':
                if (data['id'] in world_objects) {
                    world_objects[data['id']].update(data['data'])
                }
                break
            case 'function':
                if (data['id'] in world_objects) {
                    let fun = world_objects[data['id']][data['function']]
                    fun(...data['arguments'])
                }
        }
    }

    // -----------------------------------------------------------------------------------------------------------------
    addObject(object_id, object_class, config){

        console.log("Adding object with id " + object_id + " and class " + object_class)

            let babylon_object_name
            if (object_class in this.config['object_mappings']){
                babylon_object_name = this.config['object_mappings'][object_class]['BabylonObject']
                var objectPtr = eval(babylon_object_name);
                var object_config = {...config, ...this.config['object_mappings'][object_class]['config']}}
                world_objects[object_id] = new objectPtr(this.scene, object_id, object_config)

    }
    removeObject(object_id){
        console.log("Remove " + object_id)
        if (object_id in world_objects) {
            console.log("Found him")
            world_objects[object_id].delete()
            delete world_objects[object_id]
        }
    }



}