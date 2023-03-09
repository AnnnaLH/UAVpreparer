# -*- coding: utf-8 -*-

"""
/***************************************************************************
 UAVPreparerProcessing
                                 A QGIS plugin
 This plugin examines height properties on a DSM
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2023-03-09
        copyright            : (C) 2023 by Anna Lunde Hermansson
        email                : anna.lunde.hermansson@chalmers.se
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Anna Lunde Hermansson'
__date__ = '2023-03-09'
__copyright__ = '(C) 2023 by Anna Lunde Hermansson'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterField,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterFileDestination)
import numpy as np
from osgeo import gdal
import os


class UAVPreparerProcessingAlgorithm(QgsProcessingAlgorithm):
    """
    This is an example algorithm that takes a vector layer and
    creates a new identical one.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT_DSM = 'INPUT_DSM'
    INPUT_POINT = 'INPUT_POINT'
    ID_FIELD = 'ID_FIELD'
    RADIUS = 'RADIUS'
    OUTPUT_FILE = 'OUTPUT_FILE'

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source. It can have any kind of
        # geometry.
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT_DSM,
                self.tr('Digital Surface Model')
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_POINT,
                self.tr('Input Point Layer'),
                [QgsProcessing.TypeVectorPoint]
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.ID_FIELD,
                self.tr('ID field'),
                '',
                self.INPUT_POINT,
                QgsProcessingParameterField.Numeric
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.RADIUS,
                self.tr('Radius (m)'),
                QgsProcessingParameterNumber.Double, 
                100, 
                False
            )
        )

        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT_FILE,
                self.tr('Output file with tabular metric information'),
                self.tr('TXT files (*.txt *.txt)')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        vlayer = self.parameterAsVectorLayer(parameters, self.INPUT_POINT, context)
        idField = self.parameterAsFields(parameters, self.ID_FIELD, context)
        dsm_layer = self.parameterAsRasterLayer(parameters, self.INPUT_DSM, context)
        radius = self.parameterAsDouble(parameters, self.RADIUS, context)
        outputFile = self.parameterAsFileOutput(parameters, self.OUTPUT_FILE, context)
        
        provider = dsm_layer.dataProvider()
        filepath_dsm = str(provider.dataSourceUri())
        idx = vlayer.fields().indexFromName(idField[0])
        numfeat = vlayer.featureCount()
        result = np.zeros([numfeat, 4])

        i = 0
        for f in vlayer.getFeatures():
            if feedback.isCanceled():
                break
            feedback.setProgress(int((i * 100) / numfeat))

            y = f.geometry().centroid().asPoint().y()
            x = f.geometry().centroid().asPoint().y()

            filepath_tempdsm = "C:/temp/clipdsm.tif"
            bbox = (x - radius, y+radius, x+radius,y-radius)
            bigraster = gdal.Open(filepath_dsm)
            gdal.Translate(filepath_tempdsm, bigraster, projWin=bbox)
            bigraster = None
            data = gdal.Open(filepath_tempdsm)

            mat = np.array(data.ReadAsArray())

            result[i, 0] = int(f.attributes()[idx])
            result[i, 1] = mat.mean()
            result[i, 2] = mat.max()
            result[i, 3] = mat.min()


            i += 1
        headertext = 'ID MEAN MAX MIN'
        numformat = '%d' + '%6.2f' * 3
        np.savetxt(outputFile, result, fmt=numformat, delimiter = ' ', header=headertext)

        feedback.setProgressText('UAV Preparer. Operation successful!')
        return{self.OUTPUT_FILE:outputFile}



    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'UAV Preparer for Processing'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr(self.name())

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr(self.groupId())

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return ''

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return UAVPreparerProcessingAlgorithm()
