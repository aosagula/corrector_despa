from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from ..models.document import ConfigurableAttribute
from difflib import SequenceMatcher
import re


class ComparisonService:
    """Servicio para comparar documentos según atributos configurables"""

    def __init__(self):
        pass

    def compare_documents(
        self,
        commercial_data: Dict[str, Any],
        provisional_data: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """
        Compara los datos de un documento provisorio con un documento comercial

        Args:
            commercial_data: Datos extraídos del documento comercial
            provisional_data: Datos extraídos del documento provisorio
            db: Sesión de base de datos

        Returns:
            Dict con el resultado de la comparación
        """
        # Obtener atributos configurables
        attributes = db.query(ConfigurableAttribute).all()

        comparisons = []
        matches = 0
        total_comparisons = 0

        for attr in attributes:
            attr_key = attr.attribute_key
            commercial_value = self._get_nested_value(commercial_data, attr_key)
            provisional_value = self._get_nested_value(provisional_data, attr_key)

            # Si el atributo es requerido y no está presente, marcar como no coincidente
            if attr.is_required and (commercial_value is None or provisional_value is None):
                comparisons.append({
                    "attribute_name": attr.attribute_name,
                    "attribute_key": attr_key,
                    "commercial_value": commercial_value,
                    "provisional_value": provisional_value,
                    "match": False,
                    "confidence": 0.0,
                    "required": True,
                    "reason": "Campo requerido faltante"
                })
                total_comparisons += 1
                continue

            # Si ambos valores existen, compararlos
            if commercial_value is not None and provisional_value is not None:
                match, confidence = self._compare_values(
                    commercial_value,
                    provisional_value,
                    attr.validation_rules
                )

                comparisons.append({
                    "attribute_name": attr.attribute_name,
                    "attribute_key": attr_key,
                    "commercial_value": commercial_value,
                    "provisional_value": provisional_value,
                    "match": match,
                    "confidence": confidence,
                    "required": bool(attr.is_required)
                })

                total_comparisons += 1
                if match:
                    matches += 1

        # Calcular porcentaje de coincidencia
        match_percentage = (matches / total_comparisons * 100) if total_comparisons > 0 else 0

        # Determinar estado
        status = self._determine_status(match_percentage, comparisons)

        return {
            "comparisons": comparisons,
            "match_percentage": round(match_percentage, 2),
            "matches": matches,
            "total_comparisons": total_comparisons,
            "status": status
        }

    def _get_nested_value(self, data: Dict[str, Any], key: str) -> Any:
        """
        Obtiene un valor de un diccionario usando notación de punto (ej: "cliente.nombre")

        Args:
            data: Diccionario con los datos
            key: Clave usando notación de punto

        Returns:
            Valor encontrado o None
        """
        keys = key.split('.')
        value = data

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return None

            if value is None:
                return None

        return value

    def _compare_values(
        self,
        value1: Any,
        value2: Any,
        validation_rules: Dict[str, Any] = None
    ) -> Tuple[bool, float]:
        """
        Compara dos valores y retorna si coinciden y el nivel de confianza

        Args:
            value1: Primer valor
            value2: Segundo valor
            validation_rules: Reglas de validación opcionales

        Returns:
            Tupla (match, confidence)
        """
        # Convertir a strings para comparación
        str1 = str(value1).strip().lower()
        str2 = str(value2).strip().lower()

        # Comparación exacta
        if str1 == str2:
            return True, 1.0

        # Comparación de similitud de texto
        similarity = SequenceMatcher(None, str1, str2).ratio()

        # Si la similitud es mayor a 0.8, considerarlo match
        if similarity >= 0.8:
            return True, similarity

        # Aplicar reglas de validación personalizadas si existen
        if validation_rules:
            # Ejemplo: tolerancia numérica
            if validation_rules.get("type") == "numeric":
                try:
                    num1 = float(re.sub(r'[^\d.]', '', str(value1)))
                    num2 = float(re.sub(r'[^\d.]', '', str(value2)))
                    tolerance = validation_rules.get("tolerance", 0.01)

                    if abs(num1 - num2) <= tolerance:
                        return True, 0.95

                except (ValueError, TypeError):
                    pass

            # Ejemplo: comparación de fechas con formato flexible
            if validation_rules.get("type") == "date":
                # Normalizar fechas y comparar
                date1 = self._normalize_date(str1)
                date2 = self._normalize_date(str2)

                if date1 == date2:
                    return True, 0.95

        return False, similarity

    def _normalize_date(self, date_str: str) -> str:
        """
        Normaliza una fecha a formato estándar

        Args:
            date_str: String con fecha

        Returns:
            Fecha normalizada
        """
        # Extraer números de la fecha
        numbers = re.findall(r'\d+', date_str)

        if len(numbers) >= 3:
            return '-'.join(numbers[:3])

        return date_str

    def _determine_status(self, match_percentage: float, comparisons: List[Dict]) -> str:
        """
        Determina el estado de la comparación según el porcentaje de coincidencia

        Args:
            match_percentage: Porcentaje de coincidencia
            comparisons: Lista de comparaciones individuales

        Returns:
            Estado: approved, rejected, pending_review
        """
        # Verificar si algún campo requerido no coincide
        for comp in comparisons:
            if comp.get("required") and not comp.get("match"):
                return "rejected"

        # Determinar estado según porcentaje
        if match_percentage >= 90:
            return "approved"
        elif match_percentage >= 70:
            return "pending_review"
        else:
            return "rejected"


comparison_service = ComparisonService()
