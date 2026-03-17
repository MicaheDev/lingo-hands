import { useRef, useEffect } from "react";
import { useGLTF, useAnimations } from "@react-three/drei";
import * as THREE from "three";

/**
 * References & Documentation:
 * https://gltf.pmnd.rs/ (GLTF to JSX Converter)
 * https://threejs.org/ (Core Library)
 * https://r3f.docs.pmnd.rs/ (React Three Fiber Docs)
 */


// Code generating by https://gltf.pmnd.rs/ (GLTF to JSX Converter) and AI (Google gemini)

// Dynamic path selection based on environment (Vite/Dev vs Flask/Production)
const modelPath = import.meta.env.DEV 
  ? '/Dummy.glb'           // Development: Root public folder
  : '/static/dist/Dummy.glb'; // Production: Flask static assets folder

/**
 * Dummy Component
 * Renders a 3D rigged model with dynamic animation switching.
 * * @param {string} animationName - The name of the animation to play (defined in the GLB file).
 * @param {Object} props - Additional React Three Fiber group properties (position, scale, etc.).
 */
export function Dummy({ animationName, ...props }) {
  const group = useRef();
  
  // 1. Load the GLTF model, materials, and internal animations
  const { nodes, materials, animations } = useGLTF(modelPath);
  
  // 2. Setup the animation mixer linked to the main group ref
  const { actions, names } = useAnimations(animations, group);

  useEffect(() => {
    /**
     * Animation Controller Logic
     * Handles switching between states (e.g., Idle -> Walking) with smooth transitions.
     */
    if (animationName && actions[animationName]) {
      // Fade out all active animations to prevent "glitchy" overlapping
      Object.values(actions).forEach((action) => action.fadeOut(0.3));

      // Reset, configure, and play the requested animation
      const currentAction = actions[animationName];
      currentAction
        .reset()
        .setEffectiveTimeScale(1)
        .setLoop(THREE.LoopRepeat, Infinity)
        .fadeIn(0.3) // Smooth transition in
        .play();

      // Cleanup function to fade out when the component unmounts or animation changes
      return () => currentAction.fadeOut(0.3);
    } else if (animationName) {
      console.warn(`Animation "${animationName}" does not exist in this model. Available: ${names}`);
    }
  }, [animationName, actions, names]);

  return (
    <group ref={group} {...props} dispose={null}>
      <group name="Scene">
        {/* Original Sketchfab Model Hierarchy */}
        <group name="Sketchfab_model" rotation={[-Math.PI / 2, 0, 0]} scale={0.018}>
          <group name="b04cd6c64ae5488199d01401973cdad9fbx" rotation={[Math.PI / 2, 0, 0]}>
            <group name="Object_2">
              <group name="RootNode">
                <group name="Object_4">
                  
                  {/* SKELETON HIERARCHY: Essential for bone-based movement */}
                  <primitive object={nodes._rootJoint} />

                  {/* SKINNED MESHES: Each mesh is bound to the skeleton via the "skeleton" prop */}
                  <skinnedMesh
                    name="Object_10"
                    geometry={nodes.Object_10.geometry}
                    material={materials.Secondary}
                    skeleton={nodes.Object_10.skeleton}
                  />
                  <skinnedMesh
                    name="Object_11"
                    geometry={nodes.Object_11.geometry}
                    material={materials.Main}
                    skeleton={nodes.Object_11.skeleton}
                  />
                  <skinnedMesh
                    name="Object_13"
                    geometry={nodes.Object_13.geometry}
                    material={materials.Secondary}
                    skeleton={nodes.Object_13.skeleton}
                  />
                  <skinnedMesh
                    name="Object_14"
                    geometry={nodes.Object_14.geometry}
                    material={materials.Main}
                    skeleton={nodes.Object_14.skeleton}
                  />
                  <skinnedMesh
                    name="Object_7"
                    geometry={nodes.Object_7.geometry}
                    material={materials.Main}
                    skeleton={nodes.Object_7.skeleton}
                  />
                  <skinnedMesh
                    name="Object_8"
                    geometry={nodes.Object_8.geometry}
                    material={materials.Secondary}
                    skeleton={nodes.Object_8.skeleton}
                  />

                </group>
              </group>
            </group>
          </group>
        </group>
      </group>
    </group>
  );
}

// Optimization: Pre-load the model to prevent visual "popping" or lag during runtime
useGLTF.preload(modelPath);