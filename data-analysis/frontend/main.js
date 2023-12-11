import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { OBJLoader } from 'three/examples/jsm/loaders/OBJLoader.js';
import { MTLLoader } from 'three/addons/loaders/MTLLoader.js';
import Papa from 'papaparse';
import Plotly from 'plotly.js-dist';

const accelerometerPlot = document.getElementById('accelerometerPlot');
const gyroscopePlot = document.getElementById('gyroscopePlot');
const quaternionsPlot = document.getElementById('quaternionsPlot');

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);

const renderer = new THREE.WebGLRenderer({ antialias: true });
// Update the size of the renderer based on the container size
const container = document.getElementById('container');
const containerRect = container.getBoundingClientRect();
renderer.setSize(containerRect.width, containerRect.height);
document.getElementById('container').appendChild(renderer.domElement);

camera.aspect = containerRect.width / containerRect.height;
camera.updateProjectionMatrix();

const controls = new OrbitControls(camera, renderer.domElement);
controls.target.set(0, 0, 0);
controls.update();

// ambient light
const ambientLight = new THREE.AmbientLight(0xffffff, 1);
scene.add(ambientLight);

// light
const light = new THREE.DirectionalLight(0xffffff, 3);
light.position.set(0, 0, 1);
scene.add(light);

let appleModel;
let animateButton;
const csvData = [];

// show origin axes of the model
// const axesHelper = new THREE.AxesHelper(100);
let numberOfMeshes = 0;
// mtl loader
const mtlLoader = new MTLLoader();
mtlLoader.load(
  '3d_models/Assembly_Smart_Apple_low.mtl',
  (materials) => {
    materials.preload();
    const objLoader = new OBJLoader();
    objLoader.setMaterials(materials);
    objLoader.load(
      '3d_models/Assembly_Smart_Apple_low.obj',
      (obj) => {
        appleModel = obj;
        // obj.add(axesHelper); // Add axes as a child of the apple model
        obj.traverse((child) => {
            if (child.isMesh) {
                numberOfMeshes++;
                // Set a base color for the mesh
                // Assign red color to odd-numbered meshes, and blue color to even-numbered meshes
                if (numberOfMeshes % 3 === 1) {
                    child.material.color.setHex(0xff0000);
                    child.material.emissive = new THREE.Color(0.5, 0, 0);

                } else {
                    child.material.color.setHex(0xffff00);
                    child.material.emissive = new THREE.Color(0.5, 0.5, 0);
                }
                child.material.needsUpdate = true;
            }
        });
        scene.add(appleModel);
      },
      (xhr) => {
        console.log((xhr.loaded / xhr.total) * 100 + '% loaded');
      },
      (error) => {
        console.log('An error happened');
      }
    );
  },
  (xhr) => {
    console.log((xhr.loaded / xhr.total) * 100 + '% loaded');
  },
  (error) => {
    console.log('An error happened');
  }
);

// rotate the model by 180 degrees around the y-axis
scene.rotation.x = Math.PI;
// white background for the scene
scene.background = new THREE.Color(0xffffff);

camera.position.z = 150;
renderer.render(scene, camera);
document.getElementById('csvInput').addEventListener('change', handleCSVFile);

function handleCSVFile(event) {
  const file = event.target.files[0];

  if (file) {
    readCSVAndEnableAnimationButton(file);
  }
}

function readCSVAndEnableAnimationButton(csvFile) {

  // Read CSV file
  Papa.parse(csvFile, {
    header: true,
    dynamicTyping: true,
    complete: (result) => {
    //   console.log('Parsed CSV data:', result.data);
      csvData.push(...result.data);
      console.log('CSV file successfully processed');

      // set pointer-events to auto
      animateButton.style.pointerEvents = 'auto';
      animateButton.style.backgroundColor = '#ff2e2e';
    },
    error: (error) => {
      console.error('Error reading CSV file:', error);
    },
  });
}
// show origin axes of the model
const xAxis = new THREE.Vector3(1, 0, 0);
const yAxis = new THREE.Vector3(0, 1, 0);
const zAxis = new THREE.Vector3(0, 0, 1);

const arrowLength = 70;
const arrowThickness = 4; // Adjust this value for the thickness of the arrow

const arrowHelperX = new THREE.ArrowHelper(xAxis, new THREE.Vector3(), arrowLength, 0xff0000, arrowThickness, arrowThickness);
const arrowHelperY = new THREE.ArrowHelper(yAxis, new THREE.Vector3(), arrowLength, 0x00ff00, arrowThickness, arrowThickness);
const arrowHelperZ = new THREE.ArrowHelper(zAxis, new THREE.Vector3(), arrowLength, 0x0000ff, arrowThickness, arrowThickness);


scene.add(arrowHelperX);
scene.add(arrowHelperY);
scene.add(arrowHelperZ);

animateButton = document.getElementById('animateButton');
animateButton.addEventListener('click', animate);
const progressBar = document.getElementById('progressBar');
const progressText = document.getElementById('progressText');

let currentRow = 0;

const clock = new THREE.Clock();
let elapsedTime = 0;
let newPos = 0;

const cum_accel_x = [];
const cum_accel_y = [];
const cum_accel_z = [];
const cum_gyro_x = [];
const cum_gyro_y = [];
const cum_gyro_z = [];
const cum_quat_x = [];
const cum_quat_y = [];
const cum_quat_z = [];
const cum_quat_w = [];
const cum_time = [];

function animate() {
  requestAnimationFrame(animate);

  controls.update();

  if (appleModel && csvData.length > 0 && currentRow < csvData.length) {
    const dataPoint = csvData[currentRow];
    if (newPos === 0) {
        const quaternion = new THREE.Quaternion();
        quaternion.set(dataPoint.quat_x, dataPoint.quat_y, dataPoint.quat_z, dataPoint.quat_w);
        appleModel.setRotationFromQuaternion(quaternion);
        // Update arrow helpers
        arrowHelperX.position.copy(appleModel.position);
        arrowHelperX.setDirection(xAxis.clone().applyQuaternion(quaternion));

        arrowHelperY.position.copy(appleModel.position);
        arrowHelperY.setDirection(yAxis.clone().applyQuaternion(quaternion));

        arrowHelperZ.position.copy(appleModel.position);
        arrowHelperZ.setDirection(zAxis.clone().applyQuaternion(quaternion));
        appendData(dataPoint);
        updatePlotly();
        // Move to the next row for the next iteration
        currentRow++;
        // Update the progress bar
        progressBar.style.width = `${currentRow / csvData.length * 100}%`;
        progressText.innerHTML = `${Math.round(currentRow / csvData.length * 100)}%`;
        newPos = 1;
        if (currentRow === csvData.length-1) {
            currentRow = 0;
            newPos = 0;
        }
    }
    // Calculate elapsed time since the last frame
    elapsedTime += clock.getDelta();
    // Check if enough time has passed based on the column 'time_diff' in the CSV file which is in seconds
    if (newPos === 1) {
        if (elapsedTime >= (csvData[currentRow+1].time_diff)) {
            // console.log(elapsedTime);
            // console.log(csvData[currentRow+1].time_diff);
        renderer.render(scene, camera);
        elapsedTime = 0; // Reset elapsed time
        newPos = 0;
        }
    }
  }
}

// Optionally, you can update the clock in your render loop if you want to control the overall animation speed
function render() {
  requestAnimationFrame(render);
  renderer.render(scene, camera);
}

// Start the render loop
render();

function appendData(newData) {
    cum_accel_x.push(newData.accel_x);
    cum_accel_y.push(newData.accel_y);
    cum_accel_z.push(newData.accel_z);
    cum_gyro_x.push(newData.gyro_x);
    cum_gyro_y.push(newData.gyro_y);
    cum_gyro_z.push(newData.gyro_z);
    cum_quat_x.push(newData.quat_x);
    cum_quat_y.push(newData.quat_y);
    cum_quat_z.push(newData.quat_z);
    cum_quat_w.push(newData.quat_w);
    cum_time.push(newData._time);
}

function updatePlotly(data, currentRecord) {
    // use cum to update the plotly, time is the x axis
    const accel_x = {
        x: cum_time,
        y: cum_accel_x,
        name: 'accel_x',
        type: 'scatter'
    };
    const accel_y = {
        x: cum_time,
        y: cum_accel_y,
        name: 'accel_y',
        type: 'scatter'
    };
    const accel_z = {
        x: cum_time,
        y: cum_accel_z,
        name: 'accel_z',
        type: 'scatter'
    };
    const gyro_x = {
        x: cum_time,
        y: cum_gyro_x,
        name: 'gyro_x',
        type: 'scatter'
    };
    const gyro_y = {
        x: cum_time,
        y: cum_gyro_y,
        name: 'gyro_y',
        type: 'scatter'
    };
    const gyro_z = {
        x: cum_time,
        y: cum_gyro_z,
        name: 'gyro_z',
        type: 'scatter'
    };
    const quat_x = {
        x: cum_time,
        y: cum_quat_x,
        name: 'quat_x',
        type: 'scatter'
    };
    const quat_y = {
        x: cum_time,
        y: cum_quat_y,
        name: 'quat_y',
        type: 'scatter'
    };
    const quat_z = {
        x: cum_time,
        y: cum_quat_z,
        name: 'quat_z',
        type: 'scatter'
    };
    const quat_w = {
        x: cum_time,
        y: cum_quat_w,
        name: 'quat_w',
        type: 'scatter'
    };
    const accelData = [accel_x, accel_y, accel_z];
    const gyroData = [gyro_x, gyro_y, gyro_z];
    const quatData = [quat_x, quat_y, quat_z, quat_w];
    const accelLayout = {
        title: 'Accelerometer Data',
        xaxis: {
            title: 'time'
        },
        yaxis: {
            title: 'Acceleration (g)'
        },
        shapes: [
            {
                type: 'line',
                x0: cum_time[0],
                x1: cum_time[cum_time.length - 1],
                y0: 2, // First horizontal line at y = 1
                y1: 2,
                line: {
                    color: 'red',
                    width: 1,
                    dash: 'dash'
                }
            },
            {
                type: 'line',
                x0: cum_time[0],
                x1: cum_time[cum_time.length - 1],
                y0: -2, // Second horizontal line at y = -1
                y1: -2,
                line: {
                    color: 'blue',
                    width: 1,
                    dash: 'dash'
                }
            }
        ]
    };
    const gyroLayout = {
        title: 'Gyroscope Data',
        xaxis: {
            title: 'time'
        },
        yaxis: {
            title: 'Angular velocity (deg/s)'
        },
        shapes: [
            {
                type: 'line',
                x0: cum_time[0],
                x1: cum_time[cum_time.length - 1],
                y0: 400, // First horizontal line at y = 1
                y1: 400,
                line: {
                    color: 'red',
                    width: 1,
                    dash: 'dash'
                }
            },
            {
                type: 'line',
                x0: cum_time[0],
                x1: cum_time[cum_time.length - 1],
                y0: -400, // Second horizontal line at y = -1
                y1: -400,
                line: {
                    color: 'blue',
                    width: 1,
                    dash: 'dash'
                }
            }
        ]
    };
    const quatLayout = {
        title: 'Quaternions Data',
        xaxis: {
            title: 'time'
        },
        yaxis: {
            title: 'Quaternions'
        }
    };
    Plotly.newPlot(accelerometerPlot, accelData, accelLayout);
    Plotly.newPlot(gyroscopePlot, gyroData, gyroLayout);
    // Plotly.newPlot(quaternionsPlot, quatData, quatLayout);
        
  }