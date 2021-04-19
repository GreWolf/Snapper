__author__ = 'gwolf'
__date__ = '2021-03-10'
__copyright__ = '(C) 2021 by gwolf'

__revision__ = '$Format:%H$'

import os
from typing import Dict, Any, Union, List

import processing
from processing.modeler.ModelerDialog import ModelerDialog
from qgis.PyQt.QtCore import QCoreApplication, QVariant

from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm, QgsSpatialIndex, QgsPointXY,
                       QgsProcessingParameterFeatureSource, QgsFeatureSource, QgsProcessingParameterFolderDestination,
                       QgsProcessingParameterFeatureSink, QgsProcessingContext, QgsProcessingFeedback,
                       QgsProcessingParameterDistance, QgsProcessingParameterCrs, QgsProcessingParameterNumber,
                       QgsProcessingMultiStepFeedback, QgsCoordinateReferenceSystem, QgsProcessingUtils, QgsExpression,
                       QgsFeatureRequest, QgsFeature, QgsVectorLayer, QgsWkbTypes, QgsVectorDataProvider, QgsField,
                       QgsGeometry, QgsRasterLayer, QgsRasterDataProvider, QgsFields, QgsProcessingParameterRasterLayer,
                       QgsProcessingFeatureSourceDefinition, QgsProject, QgsMapLayerStore, QgsDistanceArea,
                       QgsLineString, QgsPoint, QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterVectorDestination, QgsProcessingParameterBoolean)

from ...modules.optionParser import parseOptions

options = parseOptions(__file__)


class Process(QgsProcessingAlgorithm):
    CANALS = 'CANALS'
    DELIVERYPOINTS = 'DELIVERYPOINTS'

    TOLERANCECANALS = 'TOLERANCECANALS'
    TOLERANCEPOINTS = 'TOLERANCEPOINTS'

    POINTSWITHUUID = 'POINTSWITHUUID'
    SNAPPEDPOINTS = 'SNAPPEDPOINTS'
    SNAPPEDCANALS = 'SNAPPEDCANALS'

    def __init__(self, plugin_dir: str) -> None:
        self.__plugin_dir = plugin_dir

        # Загружаем готовую модель из файла
        self.snap_lines = ModelerDialog()
        self.snap_lines.loadModel(os.path.join(self.__plugin_dir, r"qgis_models", "snap_lines.model3"))

        super().__init__()

    def initAlgorithm(self, config: Dict[str, Any]) -> None:
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                name=self.CANALS,
                description='Canals',
                types=[QgsProcessing.TypeVectorLine],
                defaultValue=None
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                name=self.DELIVERYPOINTS,
                description='Delivery points',
                types=[QgsProcessing.TypeVectorPoint],
                defaultValue=None
            )
        )

        self.addParameter(
            QgsProcessingParameterDistance(
                name=self.TOLERANCECANALS,
                description='Tolerance for canals',
                parentParameterName=self.CANALS,
                defaultValue=options.get(self.TOLERANCECANALS, None)
            )
        )

        self.addParameter(
            QgsProcessingParameterDistance(
                name=self.TOLERANCEPOINTS,
                description='Tolerance for delivery points',
                parentParameterName=self.CANALS,
                defaultValue=options.get(self.TOLERANCEPOINTS, None),
                # defaultValue=None
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                name=self.POINTSWITHUUID,
                description='Delivery points with uuid4',
                type=QgsProcessing.TypeVectorAnyGeometry,
                createByDefault=True,
                defaultValue=None
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                name=self.SNAPPEDPOINTS,
                description='Snapped delivery points with intersections',
                type=QgsProcessing.TypeVectorAnyGeometry,
                createByDefault=True,
                supportsAppend=True,
                defaultValue=None
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                name=self.SNAPPEDCANALS,
                description='Snaped canals',
                type=QgsProcessing.TypeVectorAnyGeometry,
                createByDefault=True,
                defaultValue=None
            )
        )

        # self.addParameter(
        #     QgsProcessingParameterBoolean(
        #         name='VERBOSE_LOG',
        #         description='Verbose logging',
        #         optional=True,
        #         defaultValue=False
        #     )
        # )

    def processAlgorithm(self, parameters: Dict[str, Any],
                         context: QgsProcessingContext,
                         feedback: QgsProcessingFeedback) -> Union[dict, Dict[str, Any]]:
        result = dict()

        # canals: QgsFeatureSource = self.parameterAsSource(parameters, self.CANALS, context)

        tolerancepoints: float = self.parameterAsDouble(parameters, self.TOLERANCEPOINTS, context)
        tolerancecanals: float = self.parameterAsDouble(parameters, self.TOLERANCECANALS, context)

        line_field_name = "name"
        point_line_field_name = "line"

        model_feedback = QgsProcessingMultiStepFeedback(3, feedback)

        if feedback.isCanceled():
            return result

        snappedcanals_out_name = 'native:snapgeometries_1:{}'.format(self.SNAPPEDCANALS)
        intersect_out_name = 'native:fieldcalculator_1:INTERSECTIONS'
        points_with_uuid_name = 'qgis:advancedpythonfieldcalculator_1:{}'.format(self.POINTSWITHUUID)

        proc_result = processing.run(self.snap_lines.model(),
                                     {
                                         'CANALS': parameters[self.CANALS],
                                         'DELIVERYPOINTS': parameters[self.DELIVERYPOINTS],
                                         'TOLERANCECANALS': tolerancecanals,
                                         'VERBOSE_LOG': True,
                                         snappedcanals_out_name: 'TEMPORARY_OUTPUT',
                                         intersect_out_name: 'TEMPORARY_OUTPUT',
                                         points_with_uuid_name: 'TEMPORARY_OUTPUT',
                                     },
                                     context=context,
                                     feedback=model_feedback,
                                     is_child_algorithm=True)
        # TODO SNAPPEDCANALS добавить в result в конце, когда они будут порезаны по пересечениям

        print("Главная обработка сделана")

        model_feedback.setCurrentStep(1)

        if feedback.isCanceled():
            return result

        snapped_canals: QgsVectorLayer = context.takeResultLayer(
            proc_result[snappedcanals_out_name])

        intersections: QgsVectorLayer = context.takeResultLayer(
            proc_result[intersect_out_name])

        points_with_uuid: QgsVectorLayer = context.takeResultLayer(
            proc_result[points_with_uuid_name])

        (snapped_canals_sink, snapped_canals_id) = self.parameterAsSink(parameters, self.SNAPPEDCANALS,
                                                                        context, snapped_canals.fields(),
                                                                        snapped_canals.wkbType(),
                                                                        snapped_canals.sourceCrs())

        (points_with_uuid_sink, points_with_uuid_id) = self.parameterAsSink(parameters, self.POINTSWITHUUID,
                                                                            context, points_with_uuid.fields(),
                                                                            points_with_uuid.wkbType(),
                                                                            points_with_uuid.sourceCrs())

        snapped_canals_sink.addFeatures(snapped_canals.getFeatures())
        points_with_uuid_sink.addFeatures(points_with_uuid.getFeatures())

        result.update({
            self.SNAPPEDCANALS: snapped_canals_id,
            self.POINTSWITHUUID: points_with_uuid_id,
        })

        snapped_points_layers = []

        for line_name in points_with_uuid.uniqueValues(points_with_uuid.fields().indexFromName(point_line_field_name)):
            line_expression = QgsExpression().createFieldEqualityExpression(line_field_name, line_name)
            line_request = QgsFeatureRequest()
            line_request.setFilterExpression(line_expression)

            point_expression = QgsExpression().createFieldEqualityExpression(point_line_field_name, line_name)
            point_request = QgsFeatureRequest()
            point_request.setFilterExpression(point_expression)

            subset_snapped_canals = snapped_canals.materialize(line_request, model_feedback)
            subset_points_with_uuid = points_with_uuid.materialize(point_request, model_feedback)

            snapped_points_layers.append(
                processing.run("native:snapgeometries",
                               {
                                   'INPUT': subset_points_with_uuid,
                                   'REFERENCE_LAYER': subset_snapped_canals,
                                   'TOLERANCE': tolerancepoints,
                                   'BEHAVIOR': 1,
                                   'OUTPUT': 'TEMPORARY_OUTPUT'
                               },
                               context=context,
                               # feedback=model_feedback,
                               is_child_algorithm=True)['OUTPUT']
            )

        print("Цикл пройден")

        model_feedback.setCurrentStep(2)

        if feedback.isCanceled():
            return result

        snapped_points_layers.append(intersections)

        snapped_points_id = processing.run("native:mergevectorlayers",
                                           {
                                               'LAYERS': snapped_points_layers,
                                               'CRS': points_with_uuid.crs(),
                                               'OUTPUT': 'TEMPORARY_OUTPUT'
                                           },
                                           context=context,
                                           feedback=model_feedback,
                                           is_child_algorithm=True)['OUTPUT']

        snapped_points: QgsVectorLayer = context.takeResultLayer(snapped_points_id)

        (snapped_points_sink, snapped_points_id) = self.parameterAsSink(parameters, self.SNAPPEDPOINTS,
                                                                        context, snapped_points.fields(),
                                                                        snapped_points.wkbType(),
                                                                        snapped_points.sourceCrs())

        snapped_points_sink.addFeatures(snapped_points.getFeatures())


        print("Вектора объеденены")

        model_feedback.setCurrentStep(3)

        if feedback.isCanceled():
            return result

        # for point_feat in intersections.getFeatures():
        #
        #         expression1 = QgsExpression().createFieldEqualityExpression("name", point_feat["name"])
        #         expression2 = QgsExpression().createFieldEqualityExpression("name", point_feat["name_2"])
        #         expression = expression1 + " OR " + expression2
        #         request = QgsFeatureRequest()
        #         request.setFilterExpression(expression)
        #
        #         for line_feat in snapped_canals.getFeatures(request):
        #             line_feat: QgsFeature
        #
        #             line_geom = line_feat.geometry()
        #             line_geom: QgsGeometry
        #
        #             for line_geom_part in line_geom.asGeometryCollection():
        #                 line_geom_part: QgsGeometry
        #
        #                 line_points: List[QgsPointXY] = line_geom_part.asPolyline()

        # (points_with_uuid_sink, points_with_uuid_id) = self.parameterAsSink(parameters, self.SNAPPEDPOINTS,
        #                                                                     context, points_with_uuid.fields(),
        #                                                                     points_with_uuid.wkbType(),
        #                                                                     points_with_uuid.sourceCrs())
        #
        # snapped_canals_sink.addFeatures(snapped_canals.getFeatures())

        result.update({
            self.SNAPPEDPOINTS: snapped_points_id,
        })

        print(result)
        return result

    def name(self) -> str:
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'process_data'

    def displayName(self) -> str:
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.name()

    def group(self) -> str:
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.groupId()

    def groupId(self) -> str:
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'process_data'

    # def tr(self, string):
    #     return QCoreApplication.translate('Processing', string)

    def createInstance(self) -> QgsProcessingAlgorithm:
        return Process(self.__plugin_dir)
