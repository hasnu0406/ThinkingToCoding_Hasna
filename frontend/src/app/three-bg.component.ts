import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import * as THREE from 'three';

@Component({
  selector: 'app-three-bg',
  standalone: true,
  template: '<canvas #canvas class="canvas-bg"></canvas>',
  styles: [`
    :host {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      z-index: -1;
      display: block;
    }
    .canvas-bg {
      display: block;
      width: 100%;
      height: 100%;
    }
  `]
})
export class ThreeBgComponent implements OnInit, OnDestroy {
  @ViewChild('canvas') canvasRef!: ElementRef<HTMLCanvasElement>;
  
  private scene!: THREE.Scene;
  private camera!: THREE.PerspectiveCamera;
  private renderer!: THREE.WebGLRenderer;
  private animationId: number | null = null;
  private particles: THREE.Points[] = [];

  ngOnInit(): void {
    setTimeout(() => this.initThreeScene(), 100);
  }

  private initThreeScene(): void {
    const canvas = this.canvasRef.nativeElement;
    const width = window.innerWidth;
    const height = window.innerHeight;

    // Scene setup
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
    this.renderer = new THREE.WebGLRenderer({ 
      canvas, 
      alpha: true, 
      antialias: true 
    });

    this.renderer.setSize(width, height);
    this.renderer.setClearColor(0x0d1b2a, 0.1);
    this.camera.position.z = 5;

    // Create particle system
    this.createParticles();

    // Create floating geometric shapes
    this.createGeometricElements();

    // Handle resize
    window.addEventListener('resize', () => this.onWindowResize());

    // Start animation loop
    this.animate();
  }

  private createParticles(): void {
    const geometry = new THREE.BufferGeometry();
    const count = 500;
    const positions = new Float32Array(count * 3);

    for (let i = 0; i < count * 3; i += 3) {
      positions[i] = (Math.random() - 0.5) * 30;
      positions[i + 1] = (Math.random() - 0.5) * 30;
      positions[i + 2] = (Math.random() - 0.5) * 30;
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

    const material = new THREE.PointsMaterial({
      color: 0x53a3d6,
      size: 0.05,
      transparent: true,
      opacity: 0.6,
      sizeAttenuation: true
    });

    const points = new THREE.Points(geometry, material);
    this.scene.add(points);
    this.particles.push(points);
  }

  private createGeometricElements(): void {
    // Create rotating cube
    const cubeGeometry = new THREE.BoxGeometry(2, 2, 2);
    const cubeMaterial = new THREE.MeshPhongMaterial({
      color: 0xffbe5c,
      emissive: 0xff8c42,
      shininess: 100,
      transparent: true,
      opacity: 0.1
    });
    const cube = new THREE.Mesh(cubeGeometry, cubeMaterial);
    cube.position.set(-4, 2, -3);
    this.scene.add(cube);

    // Create rotating torus
    const torusGeometry = new THREE.TorusGeometry(1.5, 0.4, 16, 100);
    const torusMaterial = new THREE.MeshPhongMaterial({
      color: 0x53a3d6,
      emissive: 0x2980b9,
      shininess: 100,
      transparent: true,
      opacity: 0.08
    });
    const torus = new THREE.Mesh(torusGeometry, torusMaterial);
    torus.position.set(4, -2, -3);
    this.scene.add(torus);

    // Create sphere
    const sphereGeometry = new THREE.SphereGeometry(1.2, 32, 32);
    const sphereMaterial = new THREE.MeshPhongMaterial({
      color: 0xf57c51,
      emissive: 0xd64a38,
      shininess: 100,
      transparent: true,
      opacity: 0.06
    });
    const sphere = new THREE.Mesh(sphereGeometry, sphereMaterial);
    sphere.position.set(0, 0, -5);
    this.scene.add(sphere);

    // Store for animation
    this.particles = [cube, torus, sphere] as any;
  }

  private animate = (): void => {
    this.animationId = requestAnimationFrame(this.animate);

    // Rotate particles
    this.scene.children.forEach((child, index) => {
      if (child instanceof THREE.Mesh || child instanceof THREE.Points) {
        if (child instanceof THREE.Mesh) {
          child.rotation.x += 0.0003 * (index + 1);
          child.rotation.y += 0.0005 * (index + 1);
          child.position.y += Math.sin(Date.now() * 0.0001 * (index + 1)) * 0.001;
        }
      }
    });

    this.renderer.render(this.scene, this.camera);
  };

  private onWindowResize(): void {
    const width = window.innerWidth;
    const height = window.innerHeight;

    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
  }

  ngOnDestroy(): void {
    if (this.animationId) {
      cancelAnimationFrame(this.animationId);
    }
    this.renderer.dispose();
  }
}
