#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import sys, re, os, dicom
import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import numpy as np 
try:
  NUMPY_AVAILABLE = True
  import vtk.util.numpy_support
except:
  NUMPY_AVAILABLE = False
from MultiVolumeImporterLib.Helper import Helper
import math

#El módulo de Registro usará un multivolumen previamente importado en Slicer 3D, podrá seleccionarse el multivolumen previamente cargado y el tipo de registro a aplicar, que puede ser: rígido, afin, Bspline, rígido-afin o rigido-Bspline. Posterior a la selección de esto se deberá proceder a dar click en el boton "Registrar".
#Lo que se obtiene después del registro es el nodo de la transformada aplicada que tendrá como atríbutos distintos parámetros asociados al desplazamiento y al escalamiento de la transformada,
#además del multivolumen después de registro

class final_Imagenes(ScriptedLoadableModule):


  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Perfusion Curves"
    self.parent.categories = ["PDI"]
    self.parent.dependencies = []
    self.parent.contributors = ["Paula Morales, Katerine Munoz"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText ="""El módulo de Registro usará un multivolumen previamente importado en Slicer 3D, podrá seleccionarse el multivolumen previamente cargado y el tipo de registro a aplicar, que puede ser: rígido, afin, Bspline, rígido-afin o rigido-Bspline. Posterior a la selección de esto se deberá proceder a dar click en el boton "Registrar".
Lo que se obtiene después del registro es el nodo de la transformada aplicada que tendrá como atríbutos distintos parámetros asociados al desplazamiento y al escalamiento de la transformada,
además del multivolumen después de registro""" 

    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """This module was developed by Paula Morales and Katerine Muñoz with support of John fredy Ochoa for
digital processing image subject in the University of Antioquia at 2018"""

class final_ImagenesWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """
  global banderaReg
  banderaReg=0
  def setup(self):

    ####################IMPORTAR VOLUMEN 4D#################################################3

### Se crea la sección para importar
    importDataCollapsibleButton = ctk.ctkCollapsibleButton()
    importDataCollapsibleButton.text = "Import Volume"
    self.layout.addWidget(importDataCollapsibleButton)
    importDataFormLayout = qt.QFormLayout(importDataCollapsibleButton)
#### Crear desplegable para seleccionar dirección del volumen
    self.__fDialog = ctk.ctkDirectoryButton()
    self.__fDialog.caption = 'Input directory'
    importDataFormLayout.addRow('Input directory:', self.__fDialog)
#### Crear desplegable para seleccionar dirección del volumen
    self.inputImportSelector = slicer.qMRMLNodeComboBox()
    self.inputImportSelector.nodeTypes = ['vtkMRMLMultiVolumeNode']
    self.inputImportSelector.addEnabled = True  # Se habilita la posibildad al usuario de crear un nuevo nodo con este widget
    self.inputImportSelector.removeEnabled = True  # Se le quita al usuario la posibilidad de eliminar el nodo seleccionado en ese momento
    self.inputImportSelector.setMRMLScene(slicer.mrmlScene)
    importDataFormLayout.addRow("Input node:", self.inputImportSelector)
    self.parent.connect('mrmlSceneChanged(vtkMRMLScene*)', self.inputImportSelector, 'setMRMLScene(vtkMRMLScene*)')

    self.__nameFrame = qt.QLineEdit()
    self.__nameFrame.text = 'NA'
    importDataFormLayout.addRow('Volume Name', self.__nameFrame)

        # Botón de importar
    self.buttonImport = qt.QPushButton("Import")
    self.buttonImport.toolTip = "Run the algorithm."
    importDataFormLayout.addRow("", self.buttonImport)
    self.buttonImport.connect('clicked(bool)', self.importFunction)

    #Por medio de esta función se crean los widgets de interacción con el usuario del modulo
    #La sección Parameters tendrá disponible un desplegable en el cual se encuentran los multivoumenes importadps
    #También poseerá un desplegable de tipo de registro los cuales serán: "Rigido", "BSpline", "Afín", "Rigido-BSpline" y "Rigido-Afin"
    #Finalemente dispondrá de un botón "Registrar" con el cual se da inicio al registro seleccionado del multivolumen cargado 
    ScriptedLoadableModuleWidget.setup(self)
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Volume registration"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    self.inputSelector = slicer.qMRMLNodeComboBox()#permite crear un desplegable con opcioneas a elegir, en este caso será el de multivolumen
    self.inputSelector.nodeTypes = ['vtkMRMLMultiVolumeNode']
    self.inputSelector.addEnabled = True  # Se habilita la posibildad al usuario de crear un nuevo nodo con este widget
    self.inputSelector.removeEnabled = False  # Se le quita al usuario la posibilidad de eliminar el nodo seleccionado en ese momento
    self.inputSelector.setMRMLScene(slicer.mrmlScene)
    parametersFormLayout.addRow("MultiVolume Node:", self.inputSelector)
    self.parent.connect('mrmlSceneChanged(vtkMRMLScene*)', self.inputSelector, 'setMRMLScene(vtkMRMLScene*)')  

    self.typeComboBox=ctk.ctkComboBox()#permite crear un desplegable con opcioneas a elegir, en este caso será el de tipo de registro
    self.typeComboBox.addItem('Rigid')#opción que de tipo de registro que puede elegir el usuario
    self.typeComboBox.addItem('BSpline')#opción que de tipo de registro que puede elegir el usuario
    self.typeComboBox.addItem('Affine')#opción que de tipo de registro que puede elegir el usuario
    self.typeComboBox.addItem('Rigid-BSpline')#opción que de tipo de registro que puede elegir el usuario
    self.typeComboBox.addItem('Rigid-Affine')#opción que de tipo de registro que puede elegir el usuario
    parametersFormLayout.addRow('Registration Type:', self.typeComboBox)  #añade el desplegable al Layout de parameter

#    self.buttonRegister = qt.QPushButton("Registrar") #creación del botón con nombre registrar
#    self.buttonRegister.toolTip = "Run the algorithm."
#    self.buttonRegister.enabled = True
#    parametersFormLayout.addRow(self.buttonRegister)#añade el boton al layout de parameter

#    self.buttonRegister.connect('clicked(bool)', self.registrarButton)#conecta el boton con la función registrarButto
#    self.layout.addStretch(1)
        #Boton ajustar
    self.buttonRegister = qt.QPushButton(u"Register")
    self.buttonRegister.toolTip = u"ajustar imágenes para facilitar el registro"
    parametersFormLayout.addWidget(self.buttonRegister)
    self.buttonRegister.connect('clicked(bool)', self.registrarButton)
    self.buttonRegister.enabled = True
    self.layout.addStretch(1)

##CURVAS
    ScriptedLoadableModuleWidget.setup(self)
    SmoothCollapsibleButton = ctk.ctkCollapsibleButton()
    SmoothCollapsibleButton.text = "Plot curves"
    self.layout.addWidget(SmoothCollapsibleButton)
    SmoothFormLayout = qt.QFormLayout(SmoothCollapsibleButton)


    self.inputSmoothSelector = slicer.qMRMLNodeComboBox()#permite crear un desplegable con opcioneas a elegir, en este caso será el de multivolumen
    self.inputSmoothSelector.nodeTypes = ['vtkMRMLMultiVolumeNode']
    self.inputSmoothSelector.addEnabled = True  # Se habilita la posibildad al usuario de crear un nuevo nodo con este widget
    self.inputSmoothSelector.removeEnabled = False  # Se le quita al usuario la posibilidad de eliminar el nodo seleccionado en ese momento
    self.inputSmoothSelector.setMRMLScene(slicer.mrmlScene)
    SmoothFormLayout.addRow("MultiVolume Node: ", self.inputSmoothSelector)
    self.parent.connect('mrmlSceneChanged(vtkMRMLScene*)', self.inputSmoothSelector, 'setMRMLScene(vtkMRMLScene*)')  

    self.imagenMultuply = slicer.qMRMLNodeComboBox()
    self.imagenMultuply.objectName = 'imagenMovilSelector'
    self.imagenMultuply.toolTip = u'Seleccione la imagen móvil'
    self.imagenMultuply.nodeTypes = ['vtkMRMLLabelMapVolumeNode']
    self.imagenMultuply.noneEnabled = True
    self.imagenMultuply.addEnabled = False  # Se quita la posibilidad al usuario de crear un nuevo nodo con este widget
    self.imagenMultuply.removeEnabled = False  # Se le quita al usuario la posibilidad de eliminar el nodo seleccionado en ese momento
##        self.imagenMovilSelector.connect('currentNodeChanged(bool)', self.enableOrDisableRegistrarButton)
    self.imagenMultuply.setMRMLScene(slicer.mrmlScene)
    SmoothFormLayout.addRow(u"Label Mask:", self.imagenMultuply)
    self.parent.connect('mrmlSceneChanged(vtkMRMLScene*)', self.imagenMultuply, 'setMRMLScene(vtkMRMLScene*)')
    
    self.buttoncCurve = qt.QPushButton(u"Plot")
    self.buttoncCurve.toolTip = u"Suavizar imágenes dinámicas"
    SmoothFormLayout.addWidget(self.buttoncCurve)
    self.buttoncCurve.connect('clicked(bool)', self.OnCurveButton)
    self.buttoncCurve.enabled = True
    self.layout.addStretch(1)



  def OnCurveButton(self):
    if (str(self.inputSmoothSelector.currentNode()) or str(self.imagenMultuply.currentNode()))=="None":
      print('ERROR: Select Input Volume Node and Label Mask')
      qt.QMessageBox.information(slicer.util.mainWindow(),'Slicer Python','ERROR: Select Input Volume Node and Label Mask')
      
      return True
    else:
      
      mvNode = slicer.vtkMRMLMultiVolumeNode()#creación nodo multivolumen
      slicer.mrmlScene.AddNode(mvNode)#añadir a la escena el nodo
      escena = slicer.mrmlScene;
      volumen4D = self.inputSmoothSelector.currentNode()
      imagenvtk4D = volumen4D.GetImageData()
      numero_imagenes = volumen4D.GetNumberOfFrames()#numero de frames del MV 
      #print('imagenes: ' + str(numero_imagenes))
      #filtro vtk para descomponer un volumen 4D
      extract1 = vtk.vtkImageExtractComponents()
      extract1.SetInputData(imagenvtk4D)
      #matriz de transformacion
      ras2ijk = vtk.vtkMatrix4x4()
      ijk2ras = vtk.vtkMatrix4x4()  
      #le solicitamos al volumen original que nos devuelva sus matrices
      volumen4D.GetRASToIJKMatrix(ras2ijk)
      volumen4D.GetIJKToRASMatrix(ijk2ras)
      #creo un volumen nuevo
      #volumenFijo = self.inputVolumeSelector.currentNode();
      #le asigno las transformaciones

      #le asigno el volumen 3D fijo
      extract1.SetComponents(0)
      extract1.Update()
      volumenFiltro = slicer.vtkMRMLScalarVolumeNode()
      volumenFiltro.SetName('Filtro')
      volumenFiltro.SetAndObserveImageData(extract1.GetOutput())
      volumenFiltro.SetRASToIJKMatrix(ras2ijk)
      volumenFiltro.SetIJKToRASMatrix(ijk2ras)
      #anado el nuevo volumen a la escena
      escena.AddNode(volumenFiltro)

      volumenSalida = slicer.vtkMRMLScalarVolumeNode();#creacion de volumen de salida
      slicer.mrmlScene.AddNode(volumenSalida)
      j=1
      bandera=0


      frameLabelsAttr=''
      volumeLabels = vtk.vtkDoubleArray()
      volumeLabels.SetNumberOfTuples(numero_imagenes)
      volumeLabels.SetNumberOfComponents(1)
      volumeLabels.Allocate(numero_imagenes)
      
      mvImage = vtk.vtkImageData()
      mvImage.SetExtent(volumenFiltro.GetImageData().GetExtent())##Se le asigna la dimension del miltuvolumen   
      mvImage.AllocateScalars(volumenFiltro.GetImageData().GetScalarType(), numero_imagenes)##Se le asigna el tipo y numero de cortes al multivolumen
      mvImageArray = vtk.util.numpy_support.vtk_to_numpy(mvImage.GetPointData().GetScalars())## Se crea la matriz de datos donde va a ir la imagen

      mat = vtk.vtkMatrix4x4()

      ##Se hace la conversion y se obtiene la matriz de transformacion del nodo
      volumenFiltro.GetRASToIJKMatrix(mat)
      mvNode.SetRASToIJKMatrix(mat)
      volumenFiltro.GetIJKToRASMatrix(mat)
      mvNode.SetIJKToRASMatrix(mat)
  ##    
      vector_int=[]
      for i in range(numero_imagenes):
        # extraigo la imagen movil
        extract1.SetComponents(i) #Seleccionar un volumen lejano
        extract1.Update()
        #Creo un volumen movil, y realizamos el mismo procedimiento que con el fijo

        volumenFiltro.SetAndObserveImageData(extract1.GetOutput())
        volumenFiltro.SetName('Filtrado')
        escena.AddNode(volumenFiltro)
        
        #parametros para la operacion de registro que seran entregados al modulo cli "brainsfit" segun tipo de registro
        parameters = {}
        parameters['Conductance']=1;
        parameters['numberOfIterations']=5;
        parameters['timeStep']=0.0625;
        parameters['inputVolume']=volumenFiltro.GetID();
        parameters['outputVolume']=volumenFiltro.GetID();      
        cliNode = slicer.cli.run( slicer.modules.gradientanisotropicdiffusion,None,parameters,wait_for_completion=True)
        
        slicer.util.saveNode(volumenFiltro,'volumenFilter'+str(i)+'.nrrd')
        
        vol = slicer.vtkMRMLScalarVolumeNode();
        escena = slicer.mrmlScene;
        vol.SetName('salida') 
        escena.AddNode(vol)
        Label=self.imagenMultuply.currentNode()
        Label=slicer.util.getNode('vtkMRMLLabelMapVolumeNode1')
        
        #parametros para la operacion de registro
        parameters = {}
        parameters['inputVolume1'] = escena.GetNodeByID('vtkMRMLLabelMapVolumeNode1')#dos volumenes de la escena, uno de ellos debe ser la mascara creada en el EDITOR
        parameters['inputVolume2'] =volumenFiltro
        parameters['outputVolume'] = vol;
        cliNode = slicer.cli.run( slicer.modules.multiplyscalarvolumes,None,parameters, wait_for_completion=True)
        slicer.util.saveNode(vol,'volumenMulty'+str(i)+'.nrrd')
        print(vol)
        a = slicer.util.arrayFromVolume(vol)
        intensidad=np.mean(a[:])
        vector_int.append(intensidad)

     # Switch to a layout (24) that contains a Chart View to initiate the construction of the widget and Chart View Node
      lns = slicer.mrmlScene.GetNodesByClass('vtkMRMLLayoutNode')
      lns.InitTraversal()
      ln = lns.GetNextItemAsObject()
      ln.SetViewArrangement(24)

      # Get the Chart View Node
      cvns = slicer.mrmlScene.GetNodesByClass('vtkMRMLChartViewNode')
      cvns.InitTraversal()
      cvn = cvns.GetNextItemAsObject()

      # Create an Array Node and add some data
      dn = slicer.mrmlScene.AddNode(slicer.vtkMRMLDoubleArrayNode())
      a = dn.GetArray()
      a.SetNumberOfTuples(numero_imagenes)
      x = range(0, 600)
      i=0
      for i in range(numero_imagenes):
          a.SetComponent(i, 0,i )
          a.SetComponent(i, 1, vector_int[i])
          a.SetComponent(i, 2, 0)




      # Create a Chart Node.
      cn = slicer.mrmlScene.AddNode(slicer.vtkMRMLChartNode())

      # Add the Array Nodes to the Chart. The first argument is a string used for the legend and to refer to the Array when setting properties.
      cn.AddArray('Prostate perfusion', dn.GetID())

      # Set a few properties on the Chart. The first argument is a string identifying which Array to assign the property. 
      # 'default' is used to assign a property to the Chart itself (as opposed to an Array Node).
      cn.SetProperty('default', 'title', 'Perfusion curves')
      cn.SetProperty('default', 'xAxisLabel', 'Time (s)')
      cn.SetProperty('default', 'yAxisLabel', 'Intensity')

      # Tell the Chart View which Chart to display
      cvn.SetChartNodeID(cn.GetID())



  def registrarButton(self):
    
    #La función registrarButton permitirá recuperar información del multivolumen,
    #la creación de nodos tipo "ScalarVolumeNode" y "MultiVolumeNode" donde estarán asociados
    #las matrices de transformación del multivolumen importado. El primer volumen será nombrado
    #como 'Fijo' y los demás serán volumen tipo 'Móvil'. Se añaden los mismos a la escena creada previamente.
    #Se creará un multivolumen que sera el reconstruido a partir del registro y se empezará a extraer componente a
    #componente del multivolumen importado, esto se repite desde el frame 0 hasta el numero de frame totales.
    #Se añaden a la escena atributos que brindan información sobre la transformada.
    #Se podrá entonces implementar el modulo cli de registro "brainsfit", que tomará los parámetros de entrada y
    #aplicará el correspondiente tipo de registro al multivolumen seleccionado.
    #Finalmente, se recuperarán los datos de desplazamiento por medio de la matriz de transformación y el volumen de salida se usará
    #para hacer la reconstrucción del multivolumen añadiendo un nodo de visualización. Se mostrarán los volumenes con desplazamiento mayor de 1 mm.
    if str(self.inputSelector.currentNode())=='None':
      print('ERROR:Select Input Volume Node')
      qt.QMessageBox.information(slicer.util.mainWindow(),'Slicer Python','ERROR:Select Input Volume Node')
      return True
      
    else:

      Tipo_registro=self.typeComboBox.currentText#el tipo de registro seleccionado previamente en el layout de parameters
      mvNode = slicer.vtkMRMLMultiVolumeNode()#creación nodo multivolumen
      slicer.mrmlScene.AddNode(mvNode)#añadir a la escena el nodo
      escena = slicer.mrmlScene;
      volumen4D = self.inputSelector.currentNode()
      imagenvtk4D = volumen4D.GetImageData()
      numero_imagenes = volumen4D.GetNumberOfFrames()#numero de frames del MV 
      print('imagenes: ' + str(numero_imagenes))
      #filtro vtk para descomponer un volumen 4D
      extract1 = vtk.vtkImageExtractComponents()
      extract1.SetInputData(imagenvtk4D)
      #matriz de transformacion
      ras2ijk = vtk.vtkMatrix4x4()
      ijk2ras = vtk.vtkMatrix4x4()  
      #le solicitamos al volumen original que nos devuelva sus matrices
      volumen4D.GetRASToIJKMatrix(ras2ijk)
      volumen4D.GetIJKToRASMatrix(ijk2ras)
      #creo un volumen nuevo
      #volumenFijo = self.inputVolumeSelector.currentNode();
      #le asigno las transformaciones

      #le asigno el volumen 3D fijo
      extract1.SetComponents(0)
      extract1.Update()
      volumenFijo = slicer.vtkMRMLScalarVolumeNode()
      volumenFijo.SetName('Fijo')
      volumenFijo.SetAndObserveImageData(extract1.GetOutput())
      volumenFijo.SetRASToIJKMatrix(ras2ijk)
      volumenFijo.SetIJKToRASMatrix(ijk2ras)
      #anado el nuevo volumen a la escena
      escena.AddNode(volumenFijo)
      vol_desp=[]
      volumenSalida = slicer.vtkMRMLScalarVolumeNode();#creacion de volumen de salida
      slicer.mrmlScene.AddNode(volumenSalida)
      j=1
      bandera=0


      frameLabelsAttr=''
      volumeLabels = vtk.vtkDoubleArray()
      volumeLabels.SetNumberOfTuples(numero_imagenes)
      volumeLabels.SetNumberOfComponents(1)
      volumeLabels.Allocate(numero_imagenes)
      
      mvImage = vtk.vtkImageData()
      mvImage.SetExtent(volumenFijo.GetImageData().GetExtent())##Se le asigna la dimension del miltuvolumen   
      mvImage.AllocateScalars(volumenFijo.GetImageData().GetScalarType(), numero_imagenes)##Se le asigna el tipo y numero de cortes al multivolumen
      mvImageArray = vtk.util.numpy_support.vtk_to_numpy(mvImage.GetPointData().GetScalars())## Se crea la matriz de datos donde va a ir la imagen

      mat = vtk.vtkMatrix4x4()

      ##Se hace la conversion y se obtiene la matriz de transformacion del nodo
      volumenFijo.GetRASToIJKMatrix(mat)
      mvNode.SetRASToIJKMatrix(mat)
      volumenFijo.GetIJKToRASMatrix(mat)
      mvNode.SetIJKToRASMatrix(mat)
  ##    
      for i in range(numero_imagenes):
        # extraigo la imagen movil
        extract1.SetComponents(i) #Seleccionar un volumen lejano
        extract1.Update()
        #Creo un volumen movil, y realizamos el mismo procedimiento que con el fijo
        volumenMovil = slicer.vtkMRMLScalarVolumeNode();
        volumenMovil.SetRASToIJKMatrix(ras2ijk)
        volumenMovil.SetIJKToRASMatrix(ijk2ras)
        volumenMovil.SetAndObserveImageData(extract1.GetOutput())
        volumenMovil.SetName('movil')
        escena.AddNode(volumenMovil)
        
        
        #creamos la transformada para alinear los volumenes
   
        transformadaSalidaBSpline=slicer.vtkMRMLBSplineTransformNode();
        transformadaSalidaBSpline.SetName('Transformada de registro BSpline'+str(i+1))
        slicer.mrmlScene.AddNode(transformadaSalidaBSpline)
      
        transformadaSalidaLinear=slicer.vtkMRMLLinearTransformNode()        
        transformadaSalidaLinear.SetName('Transformada de registro Lineal'+str(i+1))
        slicer.mrmlScene.AddNode(transformadaSalidaLinear)

        
        #parametros para la operacion de registro que seran entregados al modulo cli "brainsfit" segun tipo de registro
        parameters = {}

        
        if Tipo_registro=='Rigid-BSpline':
          parameters['fixedVolume'] = volumenFijo.GetID()
          parameters['movingVolume'] = volumenMovil.GetID()
          parameters['transformType'] = 'Rigid'
          parameters['outputTransform'] = transformadaSalidaLinear.GetID()
          parameters['outputVolume']=volumenSalida.GetID()
        
          cliNode = slicer.cli.run( slicer.modules.brainsfit,None,parameters,wait_for_completion=True)
          if bandera==0:
            bandera=1
            volumenFijo=volumenSalida
            
          parameters['fixedVolume'] = volumenFijo.GetID()
          parameters['movingVolume'] = volumenSalida.GetID()
          parameters['transformType'] = 'BSpline'
          parameters['outputTransform'] = transformadaSalidaBSpline.GetID()
          parameters['outputVolume']=volumenSalida.GetID()
        
          cliNode = slicer.cli.run( slicer.modules.brainsfit,None,parameters,wait_for_completion=True)
          
          frameImage = volumenSalida.GetImageData()
          frameImageArray = vtk.util.numpy_support.vtk_to_numpy(frameImage.GetPointData().GetScalars())
          mvImageArray.T[i] = frameImageArray
          
        elif Tipo_registro=='Rigid-Affine':
          
          parameters['fixedVolume'] = volumenFijo.GetID()
          parameters['movingVolume'] = volumenMovil.GetID()
          parameters['transformType'] = 'Rigid'
          parameters['outputTransform'] = transformadaSalidaLinear.GetID()
          parameters['outputVolume']=volumenSalida.GetID()
        
          cliNode = slicer.cli.run( slicer.modules.brainsfit,None,parameters,wait_for_completion=True)
          
          Matriz=transformadaSalidaLinear.GetMatrixTransformToParent()

          
          if bandera==0:
            bandera=1
            volumenFijo=volumenSalida
            
          
          parameters['fixedVolume'] = volumenFijo.GetID()
          parameters['movingVolume'] = volumenSalida.GetID()
          parameters['transformType'] = 'Affine'
          parameters['outputTransform'] = transformadaSalidaLinear.GetID()
          parameters['outputVolume']=volumenSalida.GetID()
        
          cliNode = slicer.cli.run( slicer.modules.brainsfit,None,parameters,wait_for_completion=True)
          
          frameImage = volumenSalida.GetImageData()
          frameImageArray = vtk.util.numpy_support.vtk_to_numpy(frameImage.GetPointData().GetScalars())
          mvImageArray.T[i] = frameImageArray
          
        elif (Tipo_registro=='Rigid') or (Tipo_registro=='Bspline') or (Tipo_registro=='Affine'):
          
          
          parameters['fixedVolume'] = volumenFijo.GetID()
          parameters['movingVolume'] = volumenMovil.GetID()
          parameters['transformType'] = Tipo_registro
          if Tipo_registro=='Bspline':
            parameters['outputTransform'] = transformadaSalidaBSpline.GetID()
          else:
            parameters['outputTransform'] = transformadaSalidaLinear.GetID()
          parameters['outputVolume']=volumenSalida.GetID()

          cliNode = slicer.cli.run( slicer.modules.brainsfit,None,parameters,wait_for_completion=True)
          Parameters = {}
          Parameters['Conductance']=1;
          Parameters['numberOfIterations']=5;
          Parameters['timeStep']=0.0625;
          Parameters['inputVolume']=volumenSalida.GetID();
          Parameters['outputVolume']=volumenSalida.GetID();      
          cliNode = slicer.cli.run( slicer.modules.gradientanisotropicdiffusion,None,Parameters,wait_for_completion=True)
          
          frameImage = volumenSalida.GetImageData()
          frameImageArray = vtk.util.numpy_support.vtk_to_numpy(frameImage.GetPointData().GetScalars())
          mvImageArray.T[i] = frameImageArray
        if(i==9):
          self.VolumenReferencia=volumenSalida
          
        mvDisplayNode = slicer.mrmlScene.CreateNodeByClass('vtkMRMLMultiVolumeDisplayNode')
        mvDisplayNode.SetScene(slicer.mrmlScene)
        slicer.mrmlScene.AddNode(mvDisplayNode)
        mvDisplayNode.SetReferenceCount(mvDisplayNode.GetReferenceCount()-1)
        mvDisplayNode.SetDefaultColorMap()

        mvNode.SetAndObserveDisplayNodeID(mvDisplayNode.GetID())
        mvNode.SetAndObserveImageData(mvImage)
        mvNode.SetNumberOfFrames(numero_imagenes)

        mvNode.SetLabelArray(volumeLabels)
        mvNode.SetLabelName('na')
        mvNode.SetAttribute('MultiVolume.FrameLabels',frameLabelsAttr)
        mvNode.SetAttribute('MultiVolume.NumberOfFrames',str(numero_imagenes))
        mvNode.SetAttribute('MultiVolume.FrameIdentifyingDICOMTagName','NA')
        mvNode.SetAttribute('MultiVolume.FrameIdentifyingDICOMTagUnits','na')

        mvNode.SetName('MultiVolume Registrado')
        Helper.SetBgFgVolumes(mvNode.GetID(),None)
          
        Matriz=transformadaSalidaLinear.GetMatrixTransformToParent()

        
        #imprime en la consola los volumenes que tienen desplazamientos mayores 1 mm
        
        
          
      print('Registro completo')

      
      #al terminar el ciclo for con todos los volumenes registrados se genera una
      #ventana emergente con un mensaje("Registro completo!") y mostrando los
      #volumenes que se desplazaron mas de 4mm
      qt.QMessageBox.information(slicer.util.mainWindow(),'Slicer Python','Registro completo')
      
      return True

  def importFunction(self):
    
    self.__dicomTag = 'NA'
    self.__veLabel = 'na'
    self.__veInitial = 0
    self.__veStep = 1
    self.__te = 1
    self.__tr = 1
    self.__fa = 1
    nameFrame = self.__nameFrame.text
    
    
    # check if the output container exists
    mvNode = self.inputImportSelector.currentNode()

    fileNames = []    # file names on disk
    frameList = []    # frames as MRMLScalarVolumeNode's
    frameFolder = ""
    volumeLabels = vtk.vtkDoubleArray()
    frameLabelsAttr = ''
    frameFileListAttr = ''
    dicomTagNameAttr = self.__dicomTag
    dicomTagUnitsAttr = self.__veLabel
    teAttr = self.__te
    trAttr = self.__tr
    faAttr = self.__fa

    # each frame is saved as a separate volume
    # first filter valid file names and sort alphabetically
    frames = []
    frame0 = None
    inputDir = self.__fDialog.directory
    
    metadatos=[]
    metadato='na'
    print('hola'+str(len(os.listdir(inputDir))))
    for f in os.listdir(inputDir):
    
      if not f.startswith('.'):
        fileName = inputDir+'/'+f
        fileName1 = str(inputDir+'/'+f)
        longitudFilneName=len(fileName1)
        formato=fileName1[(longitudFilneName-3):longitudFilneName]
        if formato=='dcm':
          metadato=dicom.read_file(fileName1)
          metadatos.append(metadato)
        fileNames.append(fileName)
        
        
        
    
      self.humanSort(fileNames)
      n=0

    for fileName in fileNames:
#f: información de cada scalar volume de cada corte
      (s,f) = self.readFrame(fileName)
      
      if s:
        if not frame0:
          frame0 = f
          frame0Image = frame0.GetImageData()
          frame0Extent = frame0Image.GetExtent()
        else:    
          frameImage = f.GetImageData()
          frameExtent = frameImage.GetExtent()
          if frameExtent[1]!=frame0Extent[1] or frameExtent[3]!=frame0Extent[3] or frameExtent[5]!=frame0Extent[5]:
            continue
        frames.append(f)
        

  

    nFrames = len(frames)
    print('Successfully read '+str(nFrames)+' frames')

    if nFrames == 1:
      print('Single frame dataset - not reading as multivolume!')
      return

    # convert seconds data to milliseconds, which is expected by pkModeling.cxx line 81
    if dicomTagUnitsAttr == 's':
      frameIdMultiplier = 1000.0
      dicomTagUnitsAttr = 'ms'
    else:
      frameIdMultiplier = 1.0
    volumeLabels.SetNumberOfTuples(nFrames)
    volumeLabels.SetNumberOfComponents(1)
    volumeLabels.Allocate(nFrames)

    for i in range(nFrames):
      frameId = frameIdMultiplier*(self.__veInitial+self.__veStep*i)
      volumeLabels.SetComponent(i, 0, frameId) 
      frameLabelsAttr += str(frameId)+','
    frameLabelsAttr = frameLabelsAttr[:-1] 

    # allocate multivolume
    mvImage = vtk.vtkImageData()
    mvImage.SetExtent(frame0Extent)
    if vtk.VTK_MAJOR_VERSION <= 5: ##Versión 7
      mvImage.SetNumberOfScalarComponents(nFrames)
      print("mvImageSC: "+str(mvImage))
      mvImage.SetScalarType(frame0.GetImageData().GetScalarType())
      print("mvImageST: "+str(mvImage))
      mvImage.AllocateScalars()
      print("mvImageAllocate: "+str(mvImage))
    else:
      mvImage.AllocateScalars(frame0.GetImageData().GetScalarType(), nFrames)
      
    extent = frame0.GetImageData().GetExtent()
    numPixels = float(extent[1]+1)*(extent[3]+1)*(extent[5]+1)*nFrames
    scalarType = frame0.GetImageData().GetScalarType()
    print('Will now try to allocate memory for '+str(numPixels)+' pixels of VTK scalar type'+str(scalarType))
    print('Memory allocated successfully')
    mvImageArray = vtk.util.numpy_support.vtk_to_numpy(mvImage.GetPointData().GetScalars())


    ##EMPIEZA A FORMARCE EL VOLUMEN###############

    mat = vtk.vtkMatrix4x4()
    frame0.GetRASToIJKMatrix(mat)
    mvNode.SetRASToIJKMatrix(mat)
    frame0.GetIJKToRASMatrix(mat)
    mvNode.SetIJKToRASMatrix(mat)
    print("frameId: "+str(frameId))
    print("# imag: "+str(nFrames))
##    print("Long frame: "+str(len(frame)))
    for frameId in range(nFrames):
      # TODO: check consistent size and orientation!
      frame = frames[frameId]
      frameImage = frame.GetImageData()
      frameImageArray = vtk.util.numpy_support.vtk_to_numpy(frameImage.GetPointData().GetScalars())
      mvImageArray.T[frameId] = frameImageArray

    mvDisplayNode = slicer.mrmlScene.CreateNodeByClass('vtkMRMLMultiVolumeDisplayNode')
    mvDisplayNode.SetScene(slicer.mrmlScene)
    slicer.mrmlScene.AddNode(mvDisplayNode)
    mvDisplayNode.SetReferenceCount(mvDisplayNode.GetReferenceCount()-1)
    mvDisplayNode.SetDefaultColorMap()

    mvNode.SetAndObserveDisplayNodeID(mvDisplayNode.GetID())
    mvNode.SetAndObserveImageData(mvImage)
    mvNode.SetNumberOfFrames(nFrames)

    mvNode.SetLabelArray(volumeLabels)
    mvNode.SetLabelName(self.__veLabel)

    mvNode.SetAttribute('MultiVolume.FrameLabels',frameLabelsAttr)
    mvNode.SetAttribute('MultiVolume.NumberOfFrames',str(nFrames))
    mvNode.SetAttribute('MultiVolume.FrameIdentifyingDICOMTagName',dicomTagNameAttr)
    mvNode.SetAttribute('MultiVolume.FrameIdentifyingDICOMTagUnits',dicomTagUnitsAttr)

    if dicomTagNameAttr == 'TriggerTime' or dicomTagNameAttr == 'AcquisitionTime':
      if teAttr != '':
        mvNode.SetAttribute('MultiVolume.DICOM.EchoTime',teAttr)
      if trAttr != '':
        mvNode.SetAttribute('MultiVolume.DICOM.RepetitionTime',trAttr)
      if faAttr != '':
        mvNode.SetAttribute('MultiVolume.DICOM.FlipAngle',faAttr)

    mvNode.SetName(nameFrame)
    
    NameFrame=nameFrame
    self.Diccionario={NameFrame:metadato};
    print(self.Diccionario.get(NameFrame))
    Helper.SetBgFgVolumes(mvNode.GetID(),None)
  

  def readFrame(self,file):
    sNode = slicer.vtkMRMLVolumeArchetypeStorageNode()
    sNode.ResetFileNameList()
    sNode.SetFileName(file)
    sNode.SetSingleFile(0)
    frame = slicer.vtkMRMLScalarVolumeNode()
    success = sNode.ReadData(frame)
    return (success,frame)



  def humanSort(self,l):
    """ Sort the given list in the way that humans expect. 
        Conributed by Yanling Liu
    """ 
    convert = lambda text: int(text) if text.isdigit() else text 
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
    l.sort( key=alphanum_key )
