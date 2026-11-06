import { Route, Routes } from 'react-router-dom'
import HomePage from '@/pages/HomePage'

export default function App() {
  return (
    <div className="mx-auto min-h-dvh max-w-md bg-white">
      <Routes>
        <Route path="/" element={<HomePage />} />
      </Routes>
    </div>
  )
}
