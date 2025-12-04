"""seed_eaes_ru_section_templates

Revision ID: 3a6c93eefa06
Revises: 
Create Date: 2025-12-05 01:33:09.358463

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import datetime as dt


# revision identifiers, used by Alembic.
revision: str = '3a6c93eefa06'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    templates_table = sa.table(
        "templates",
        sa.column("name", sa.String()),
        sa.column("description", sa.String()),
        sa.column("type", sa.String()),
        sa.column("section_code", sa.String()),
        sa.column("language", sa.String()),
        sa.column("scope", sa.String()),
        sa.column("content", sa.Text()),
        sa.column("variables", sa.JSON()),
        sa.column("is_default", sa.Boolean()),
        sa.column("is_active", sa.Boolean()),
        sa.column("version", sa.Integer()),
        sa.column("created_at", sa.DateTime()),
        sa.column("updated_at", sa.DateTime()),
        sa.column("created_by", sa.String()),
    )

    now = dt.datetime.utcnow()
    seed_author = "system_seed_eaes_ru"

    op.bulk_insert(
        templates_table,
        [
            {
                "name": "ЕАЭС/РФ – Краткая характеристика исследования (Сводка)",
                "description": "Краткое резюме основных характеристик и результатов исследования в соответствии с практикой ЕАЭС/РФ.",
                "type": "section_text",
                "section_code": "SYNOPSIS",
                "language": "ru",
                "scope": "global",
                "content": (
                    "Исследование {{study_code}} представляет собой {{phase}} исследование, "
                    "направленное на оценку эффективности и безопасности препарата {{investigational_product_name}} "
                    "у пациентов с {{indication}}.\n\n"
                    "Исследование имело дизайн: {{study_design_type}} с рандомизацией в соотношении "
                    "{{randomization_ratio}} в {{treatment_arms_overview}}. Планировалось включить "
                    "примерно {{planned_sample_size}} субъектов.\n\n"
                    "Основной целью исследования было {{primary_objective_text}}. "
                    "Ключевые вторичные цели включали {{key_secondary_objectives_text}}.\n\n"
                    "Основная конечная точка: {{primary_endpoint_name}}, определяемая как "
                    "{{primary_endpoint_definition}} и оцениваемая в момент {{primary_endpoint_timepoint}}. "
                    "Ключевые вторичные конечные точки включали {{secondary_endpoints_overview}}.\n\n"
                    "Популяция для первичного анализа эффективности включала всех рандомизированных пациентов "
                    "(ITT-популяция, N={{population_ITT_N}}). Пер-протокольная (PP) популяция включала "
                    "{{population_PP_N}} пациентов, удовлетворяющих ключевым критериям протокола."
                ),
                "variables": {
                    "study_code": "Внутренний код исследования (например, ABC123).",
                    "phase": "Фаза исследования (например, III фаза).",
                    "investigational_product_name": "Наименование исследуемого лекарственного препарата.",
                    "indication": "Показание / заболевание.",
                    "study_design_type": "Описание дизайна (рандомизированное, двойное слепое и т.п.).",
                    "randomization_ratio": "Соотношение рандомизации (например, 1:1).",
                    "treatment_arms_overview": "Краткое описание схем лечения в исследуемых группах.",
                    "planned_sample_size": "Планируемое количество рандомизированных пациентов.",
                    "primary_objective_text": "Текст основной цели исследования.",
                    "key_secondary_objectives_text": "Краткое описание ключевых вторичных целей.",
                    "primary_endpoint_name": "Наименование основной конечной точки.",
                    "primary_endpoint_definition": "Операциональное определение основной конечной точки.",
                    "primary_endpoint_timepoint": "Временная точка оценки основной конечной точки.",
                    "secondary_endpoints_overview": "Краткое описание ключевых вторичных конечных точек.",
                    "population_ITT_N": "Количество пациентов в ITT-популяции.",
                    "population_PP_N": "Количество пациентов в PP-популяции.",
                },
                "is_default": True,
                "is_active": True,
                "version": 1,
                "created_at": now,
                "updated_at": now,
                "created_by": seed_author,
            },
            {
                "name": "ЕАЭС/РФ – Цели и задачи исследования",
                "description": "Шаблон текста для формулировки целей и задач исследования для досье ЕАЭС/РФ.",
                "type": "section_text",
                "section_code": "OBJECTIVES",
                "language": "ru",
                "scope": "global",
                "content": (
                    "Основной целью исследования {{study_code}} было {{primary_objective_text}} "
                    "у пациентов с {{indication}}, получавших {{investigational_product_name}}.\n\n"
                    "Ключевые вторичные цели исследования включали {{secondary_objectives_detailed}}.\n\n"
                    "Дополнительные (исследовательские) цели были направлены на {{exploratory_objectives_text}} "
                    "и предназначались для получения дополнительных данных и генерации гипотез "
                    "в рамках последующих исследований."
                ),
                "variables": {
                    "study_code": "Внутренний код исследования.",
                    "indication": "Показание / заболевание.",
                    "investigational_product_name": "Наименование исследуемого лекарственного препарата.",
                    "primary_objective_text": "Формулировка основной цели исследования.",
                    "secondary_objectives_detailed": "Список или краткое описание ключевых вторичных целей.",
                    "exploratory_objectives_text": "Описание исследовательских целей.",
                },
                "is_default": True,
                "is_active": True,
                "version": 1,
                "created_at": now,
                "updated_at": now,
                "created_by": seed_author,
            },
            {
                "name": "ЕАЭС/РФ – Дизайн исследования",
                "description": "Описание дизайна исследования в соответствии с требованиями ЕАЭС/РФ.",
                "type": "section_text",
                "section_code": "DESIGN",
                "language": "ru",
                "scope": "global",
                "content": (
                    "Исследование {{study_code}} представляло собой {{study_design_type}}, "
                    "{{blinding_description}} клиническое исследование, проводимое приблизительно "
                    "в {{number_of_centers}} центрах в {{number_of_countries}} странах.\n\n"
                    "Пациенты рандомизировались в соотношении {{randomization_ratio}} для получения "
                    "{{treatment_arms_overview}}. Рандомизация стратифицировалась по следующим факторам: "
                    "{{stratification_factors}}.\n\n"
                    "Исследование включало следующие периоды: {{study_periods_overview}}. "
                    "Плановая длительность терапии составляла {{treatment_duration}}, "
                    "общая продолжительность участия пациента в исследовании – примерно "
                    "{{total_participation_duration}}.\n\n"
                    "Схематичное представление дизайна исследования приведено в {{study_flow_reference}}."
                ),
                "variables": {
                    "study_code": "Внутренний код исследования.",
                    "study_design_type": "Тип дизайна (рандомизированное, контролируемое и т.д.).",
                    "blinding_description": "Характер ослепления (двойное слепое, открытое и т.п.).",
                    "number_of_centers": "Количество центров, участвующих в исследовании.",
                    "number_of_countries": "Количество стран, в которых проводилось исследование.",
                    "randomization_ratio": "Соотношение рандомизации.",
                    "treatment_arms_overview": "Описание исследуемых схем лечения.",
                    "stratification_factors": "Факторы стратификации (при наличии).",
                    "study_periods_overview": "Перечень периодов (скрининг, лечение, последующее наблюдение и т.п.).",
                    "treatment_duration": "Плановая длительность лечения.",
                    "total_participation_duration": "Плановая общая продолжительность участия пациента.",
                    "study_flow_reference": "Ссылка на рисунок/таблицу со схемой исследования.",
                },
                "is_default": True,
                "is_active": True,
                "version": 1,
                "created_at": now,
                "updated_at": now,
                "created_by": seed_author,
            },
            {
                "name": "ЕАЭС/РФ – Популяции и распределение пациентов",
                "description": "Распределение пациентов по популяциям и статус участия (аналоги раздела \"Subject disposition\").",
                "type": "section_text",
                "section_code": "DISPOSITION",
                "language": "ru",
                "scope": "global",
                "content": (
                    "Всего было скринировано {{screened_N}} пациентов, из них {{randomized_N}} были рандомизированы "
                    "и включены в ITT-популяцию.\n\n"
                    "Из рандомизированных пациентов {{completed_treatment_N}} ({{completed_treatment_pct}}%) "
                    "завершили период лечения, тогда как {{discontinued_treatment_N}} "
                    "({{discontinued_treatment_pct}}%) прекратили участие в лечении досрочно.\n\n"
                    "Наиболее частыми причинами прекращения лечения были {{top_discontinuation_reasons}}.\n\n"
                    "Пер-протокольная (PP) популяция включала {{pp_N}} пациентов, удовлетворяющих ключевым "
                    "критериям протокола и не имеющих существенных нарушений, влияющих на оценку эффективности."
                ),
                "variables": {
                    "screened_N": "Количество скринированных пациентов.",
                    "randomized_N": "Количество рандомизированных пациентов (ITT-популяция).",
                    "completed_treatment_N": "Количество пациентов, завершивших лечение.",
                    "completed_treatment_pct": "Доля пациентов, завершивших лечение, в процентах.",
                    "discontinued_treatment_N": "Количество пациентов, досрочно прекративших лечение.",
                    "discontinued_treatment_pct": "Доля пациентов, досрочно прекративших лечение, в процентах.",
                    "top_discontinuation_reasons": "Наиболее частые причины прекращения лечения.",
                    "pp_N": "Количество пациентов в пер-протокольной популяции.",
                },
                "is_default": True,
                "is_active": True,
                "version": 1,
                "created_at": now,
                "updated_at": now,
                "created_by": seed_author,
            },
            {
                "name": "ЕАЭС/РФ – Основные результаты по эффективности",
                "description": "Шаблон для описания первичной конечной точки и основных результатов эффективности.",
                "type": "section_text",
                "section_code": "EFFICACY_PRIMARY",
                "language": "ru",
                "scope": "global",
                "content": (
                    "Основная конечная точка исследования – {{primary_endpoint_name}}, определяемая как "
                    "{{primary_endpoint_definition}} и оцениваемая в момент {{primary_endpoint_timepoint}}.\n\n"
                    "В ITT-популяции (N={{population_ITT_N}}) среднее (SD) значение {{primary_endpoint_name_short}} "
                    "в исходном состоянии составляло {{baseline_value}} и изменилось до {{visit_value}} "
                    "в группе {{test_treatment_label}} к моменту {{primary_endpoint_timepoint}}, по сравнению "
                    "с {{comparator_visit_value}} в группе {{comparator_label}}.\n\n"
                    "Скорректированная разница между группами ({{effect_measure_label}}) составила "
                    "{{effect_estimate}} ({{effect_ci}}), p={{effect_p_value}}.\n\n"
                    "Полученные результаты {{primary_conclusion_text}} в отношении достижения основной цели исследования."
                ),
                "variables": {
                    "primary_endpoint_name": "Полное название основной конечной точки.",
                    "primary_endpoint_name_short": "Краткое обозначение конечной точки для повторного использования.",
                    "primary_endpoint_definition": "Операциональное определение основной конечной точки.",
                    "primary_endpoint_timepoint": "Временная точка анализа основной конечной точки.",
                    "population_ITT_N": "Количество пациентов в ITT-популяции.",
                    "baseline_value": "Среднее (SD) исходное значение в группе тест-препарата.",
                    "visit_value": "Среднее (SD) значение в момент оценки в группе тест-препарата.",
                    "comparator_visit_value": "Среднее (SD) значение в момент оценки в группе сравнения.",
                    "test_treatment_label": "Обозначение исследуемой терапии.",
                    "comparator_label": "Обозначение группы сравнения (плацебо/активный контроль).",
                    "effect_measure_label": "Тип оценочного показателя (разница средних, отношение шансов и т.п.).",
                    "effect_estimate": "Числовое значение эффекта лечения.",
                    "effect_ci": "Доверительный интервал (например, 95% ДИ [ниж; верх]).",
                    "effect_p_value": "p-значение для сравнения между группами.",
                    "primary_conclusion_text": "Краткий вывод по результатам (достигнута ли конечная точка и т.п.).",
                },
                "is_default": True,
                "is_active": True,
                "version": 1,
                "created_at": now,
                "updated_at": now,
                "created_by": seed_author,
            },
            {
                "name": "ЕАЭС/РФ – Общая характеристика безопасности",
                "description": "Обобщённый раздел по безопасности (частота НЯ, общая профиль безопасности).",
                "type": "section_text",
                "section_code": "SAFETY_OVERVIEW",
                "language": "ru",
                "scope": "global",
                "content": (
                    "В популяцию безопасности были включены {{safety_population_N}} пациентов, "
                    "получивших хотя бы одну дозу исследуемого препарата.\n\n"
                    "Общая частота возникновения нежелательных явлений (НЯ), связанных с лечением, "
                    "составила {{teae_overall_pct}}% в группе {{test_treatment_label}} и "
                    "{{teae_comparator_pct}}% в группе {{comparator_label}}.\n\n"
                    "Большинство НЯ были {{teae_severity_pattern}} по степени тяжести. "
                    "Наиболее часто регистрируемыми НЯ (≥{{teae_frequency_threshold}}% в любой группе) были "
                    "{{common_teae_list}}.\n\n"
                    "В целом профиль безопасности {{investigational_product_name}} в данном исследовании "
                    "соответствовал ранее известным данным и не выявил новых или неожиданных рисков."
                ),
                "variables": {
                    "safety_population_N": "Количество пациентов в популяции безопасности.",
                    "teae_overall_pct": "Процент пациентов с хотя бы одним НЯ в группе тест-препарата.",
                    "teae_comparator_pct": "Процент пациентов с хотя бы одним НЯ в группе сравнения.",
                    "test_treatment_label": "Название/обозначение тест-препарата.",
                    "comparator_label": "Название/обозначение препарата сравнения/плацебо.",
                    "teae_severity_pattern": "Распределение по степени тяжести (лёгкие/умеренные/тяжёлые).",
                    "teae_frequency_threshold": "Порог частоты НЯ для включения в список (например, 5).",
                    "common_teae_list": "Перечень наиболее часто наблюдаемых НЯ.",
                    "investigational_product_name": "Наименование исследуемого лекарственного препарата.",
                },
                "is_default": True,
                "is_active": True,
                "version": 1,
                "created_at": now,
                "updated_at": now,
                "created_by": seed_author,
            },
            {
                "name": "ЕАЭС/РФ – Серьёзные НЯ и летальные исходы",
                "description": "Раздел по серьёзным нежелательным явлениям и летальным исходам.",
                "type": "section_text",
                "section_code": "SAFETY_SAE_DEATHS",
                "language": "ru",
                "scope": "global",
                "content": (
                    "Серьёзные нежелательные явления (СНЯ) были зарегистрированы у {{sae_test_N}} "
                    "({{sae_test_pct}}%) пациентов в группе {{test_treatment_label}} и у {{sae_comparator_N}} "
                    "({{sae_comparator_pct}}%) пациентов в группе {{comparator_label}}.\n\n"
                    "Наиболее часто наблюдавшимися СНЯ были {{common_sae_list}}.\n\n"
                    "Летальные исходы были зарегистрированы у {{deaths_test_N}} "
                    "({{deaths_test_pct}}%) пациентов в группе {{test_treatment_label}} и у {{deaths_comparator_N}} "
                    "({{deaths_comparator_pct}}%) пациентов в группе {{comparator_label}}. "
                    "{{treatment_related_death_summary}}.\n\n"
                    "Никаких закономерностей в структуре СНЯ или летальных исходов, указывающих на новый "
                    "сигнал безопасности, выявлено не было."
                ),
                "variables": {
                    "sae_test_N": "Количество пациентов с хотя бы одним СНЯ в группе тест-препарата.",
                    "sae_test_pct": "Процент пациентов с СНЯ в группе тест-препарата.",
                    "sae_comparator_N": "Количество пациентов с хотя бы одним СНЯ в группе сравнения.",
                    "sae_comparator_pct": "Процент пациентов с СНЯ в группе сравнения.",
                    "test_treatment_label": "Название/обозначение тест-препарата.",
                    "comparator_label": "Название/обозначение препарата сравнения/плацебо.",
                    "common_sae_list": "Наиболее часто наблюдаемые СНЯ.",
                    "deaths_test_N": "Количество летальных исходов в группе тест-препарата.",
                    "deaths_test_pct": "Процент летальных исходов в группе тест-препарата.",
                    "deaths_comparator_N": "Количество летальных исходов в группе сравнения.",
                    "deaths_comparator_pct": "Процент летальных исходов в группе сравнения.",
                    "treatment_related_death_summary": "Краткая характеристика случаев, оценённых как связанные с лечением (если имеются).",
                },
                "is_default": True,
                "is_active": True,
                "version": 1,
                "created_at": now,
                "updated_at": now,
                "created_by": seed_author,
            },
            {
                "name": "ЕАЭС/РФ – Обсуждение и выводы по пользе/риску",
                "description": "Итоговый раздел по результатам исследования и соотношению польза/риск.",
                "type": "section_text",
                "section_code": "DISCUSSION",
                "language": "ru",
                "scope": "global",
                "content": (
                    "В данном {{phase}} исследовании препарата {{investigational_product_name}} у пациентов "
                    "с {{indication}} основная конечная точка {{primary_endpoint_name_short}} "
                    "{{primary_endpoint_outcome_summary}}.\n\n"
                    "Результаты по вторичным конечным точкам в целом {{secondary_results_overall}} и были "
                    "{{secondary_consistency_vs_primary}} по отношению к результатам по основной конечной точке.\n\n"
                    "Профиль безопасности {{investigational_product_name}}, наблюдавшийся в этом исследовании, "
                    "{{safety_profile_summary}} и был {{consistency_with_known_safety}} с ранее известными "
                    "данными по безопасности препарата.\n\n"
                    "С учётом полученных данных об эффективности и безопасности соотношение польза/риск "
                    "препарата {{investigational_product_name}} для применения у {{target_population_description}} "
                    "{{overall_benefit_risk_conclusion}}."
                ),
                "variables": {
                    "phase": "Фаза исследования (II, III и т.п.).",
                    "investigational_product_name": "Наименование исследуемого лекарственного препарата.",
                    "indication": "Показание / заболевание.",
                    "primary_endpoint_name_short": "Краткое обозначение основной конечной точки.",
                    "primary_endpoint_outcome_summary": "Краткий вывод о том, достигнута ли основная конечная точка.",
                    "secondary_results_overall": "Краткое описание результатов по вторичным конечным точкам.",
                    "secondary_consistency_vs_primary": "Комментарий о согласованности вторичных результатов с основной конечной точкой.",
                    "safety_profile_summary": "Краткая характеристика основного профиля безопасности.",
                    "consistency_with_known_safety": "Комментарий о соответствии наблюдаемого профиля безопасности ранее известным данным.",
                    "overall_benefit_risk_conclusion": "Итоговый вывод о соотношении польза/риск (благоприятное/приемлемое/неблагоприятное и т.п.).",
                    "target_population_description": "Описание целевой популяции пациентов.",
                },
                "is_default": True,
                "is_active": True,
                "version": 1,
                "created_at": now,
                "updated_at": now,
                "created_by": seed_author,
            },
        ],
    )


def downgrade() -> None:
    # При откате миграции удаляем только те шаблоны, которые были добавлены этим seed'ом
    op.execute(
        "DELETE FROM templates WHERE created_by = 'system_seed_eaes_ru'"
    )


