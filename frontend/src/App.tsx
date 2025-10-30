import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ToastContainer } from 'react-toastify'
import 'react-toastify/dist/ReactToastify.css'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Materials from './pages/Materials'
import MaterialDetail from './pages/MaterialDetail'
import ChromatographicAnalyses from './pages/ChromatographicAnalyses'
import Composites from './pages/Composites'
import CompositeDetail from './pages/CompositeDetail'
import Workflows from './pages/Workflows'
import BlueLine from './pages/BlueLine'
import BlueLineDetail from './pages/BlueLineDetail'
import BlueLineFieldLogic from './pages/BlueLineFieldLogic'
import Questionnaires from './pages/Questionnaires'
import QuestionnaireDetail from './pages/QuestionnaireDetail'
import QuestionnaireFormDynamic from './pages/QuestionnaireFormDynamic'
import QuestionnaireImport from './pages/QuestionnaireImport'

function App() {
  return (
    <BrowserRouter>
      <ToastContainer
        position="top-right"
        autoClose={3000}
        hideProgressBar={false}
        newestOnTop={false}
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme="dark"
      />
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="materials" element={<Materials />} />
          <Route path="materials/:id" element={<MaterialDetail />} />
          <Route path="analyses" element={<ChromatographicAnalyses />} />
          <Route path="composites" element={<Composites />} />
          <Route path="composites/:id" element={<CompositeDetail />} />
          <Route path="workflows" element={<Workflows />} />
          <Route path="blue-line" element={<BlueLine />} />
          <Route path="blue-line/:id" element={<BlueLineDetail />} />
          <Route path="blue-line/material/:material_id" element={<BlueLineDetail />} />
          <Route path="blue-line/field-logic" element={<BlueLineFieldLogic />} />
          <Route path="questionnaires" element={<Questionnaires />} />
          <Route path="questionnaires/new" element={<QuestionnaireFormDynamic />} />
          <Route path="questionnaires/import" element={<QuestionnaireImport />} />
          <Route path="questionnaires/:id" element={<QuestionnaireDetail />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App






