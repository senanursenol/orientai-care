import React from 'react';
import { Routes, Route } from 'react-router-dom';
import About from './About';

function Home(){
    return (
        <div>
            <h3>Welcome to OrientAI</h3>
            <Routes>
                <Route path="/about" element={<About />} />
            </Routes>
        </div>
    )
}

export default Home
