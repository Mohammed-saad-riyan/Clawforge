"""Validator module for ClawForge.

Provides Docker-based Flutter validation:
- flutter pub get (dependency resolution)
- dart run build_runner build (code generation)
- dart analyze (static analysis)
"""

from clawforge.validator.docker_validator import (
    DockerValidator,
    ValidationResult,
    ValidationError,
    ValidationStage,
    FullValidationResult,
    get_docker_validator,
)
from clawforge.validator.error_parser import (
    DartAnalyzeParser,
    parse_dart_analyze_output,
    parse_pub_get_output,
    parse_build_runner_output,
    format_errors_for_llm,
)
from clawforge.validator.validation_loop import (
    ValidationLoop,
    ValidationLoopResult,
    run_validation_loop,
    create_refiner_fix_function,
)

__all__ = [
    # Docker validator
    "DockerValidator",
    "ValidationResult",
    "ValidationError",
    "ValidationStage",
    "FullValidationResult",
    "get_docker_validator",
    # Error parsing
    "DartAnalyzeParser",
    "parse_dart_analyze_output",
    "parse_pub_get_output",
    "parse_build_runner_output",
    "format_errors_for_llm",
    # Validation loop
    "ValidationLoop",
    "ValidationLoopResult",
    "run_validation_loop",
    "create_refiner_fix_function",
]
