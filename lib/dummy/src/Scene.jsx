import { Canvas } from "@react-three/fiber";
import { OrbitControls, Environment } from "@react-three/drei";
import { Dummy } from "./Dummy";

function Scene({ signId }) {
  return (
    <Canvas
      shadows
      camera={{ position: [0, 0, 1], fov: 60, zoom: 1.2 }}
      className="scene"
    >
      {/* Environment and Lighting */}
      <ambientLight intensity={1} />
      <spotLight position={[5, 10, 5]} angle={0.3} intensity={50} castShadow />
      <Environment preset="city" />

      {/* The Animated Hand Model */}
      <Dummy animationName={signId} position={[0, -1.3, 0.5]} scale={0.5} />

      {/* OrbitControls: Allows the user to rotate the model */}
      <OrbitControls
        enableDamping
        dampingFactor={0.05}
        screenSpacePanning={false}
        minDistance={1.5}
        maxDistance={10}
      />
    </Canvas>
  );
}

export default Scene;
