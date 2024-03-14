// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyDJY8EWLnqrVGBRHqTQVPwiJ7vLiZQNgI4",
  authDomain: "portfolio-838bf.firebaseapp.com",
  projectId: "portfolio-838bf",
  storageBucket: "portfolio-838bf.appspot.com",
  messagingSenderId: "113900711061",
  appId: "1:113900711061:web:510132df09da56f4d37f9c",
  measurementId: "G-217FVHHBL3"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);