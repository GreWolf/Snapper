from typing import Union

from processing.gui.wrappers import (
    TableFieldWidgetWrapper
)

from qgis.gui import (
    QgsProcessingGui,
)

from ..modules.proximity import find_field

DIALOG_STANDARD = QgsProcessingGui.Standard
DIALOG_BATCH = QgsProcessingGui.Batch
DIALOG_MODELER = QgsProcessingGui.Modeler


class CustomFieldWrapper(TableFieldWidgetWrapper):

    def parentValueChanged(self, wrapper):
        value = wrapper.parameterValue()
        if isinstance(value, str) and value in self.parent_file_based_layers:
            self.setLayer(self.parent_file_based_layers[value])
        else:
            self.setLayer(value)
            if isinstance(value, str):
                self.parent_file_based_layers[value] = self._layer

        out_fields: Union[str, list] = []

        if self._layer and self.parameterDefinition().defaultValue():
            default_value = self.parameterDefinition().defaultValue()
            if isinstance(default_value, (list, set, tuple, dict)):
                for defautl_field in default_value:
                    outfield = find_field(defautl_field, self._layer.fields().names())
                    out_fields.append(outfield)

            elif isinstance(default_value, str):
                outfield = find_field(default_value, self._layer.fields().names())
                out_fields = outfield
        else:
            out_fields = self.parameterDefinition().defaultValue()

        self.setValue(out_fields)

    def postInitialize(self, wrappers):
        for wrapper in wrappers:
            if wrapper.parameterDefinition().name() == self.parameterDefinition().parentLayerParameterName():
                if self.dialogType in (DIALOG_STANDARD, DIALOG_BATCH):
                    self.setLayer(wrapper.parameterValue())
                    # self.parentValueChanged(wrapper)
                    wrapper.widgetValueHasChanged.connect(self.parentValueChanged)
                break
