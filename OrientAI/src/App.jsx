import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Home from './routes/Home'
import About from './routes/About'

function App() {
  return (
    <BrowserRouter>
    <Routes>
        <Route path="/" element={<Home />} context="To Home"/>
        <Route path="/about" element={<About />} context="To About"/>
    </Routes>
    </BrowserRouter>

  )
}

export default App