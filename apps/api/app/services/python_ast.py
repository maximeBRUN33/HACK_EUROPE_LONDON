from __future__ import annotations

import ast
import logging
import os
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

IGNORED_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}
ENTITY_TOKENS = {
    "customer": "Customer",
    "client": "Customer",
    "lead": "Lead",
    "opportunity": "Lead",
    "order": "Order",
    "invoice": "Invoice",
    "payment": "Payment",
    "stock": "Stock",
    "inventory": "Stock",
    "ledger": "Ledger",
    "account": "Account",
    "shipment": "Shipment",
}
CRUD_TOKENS = {
    "create": "create",
    "insert": "create",
    "add": "create",
    "save": "update",
    "update": "update",
    "write": "update",
    "set": "update",
    "delete": "delete",
    "remove": "delete",
    "unlink": "delete",
    "get": "read",
    "fetch": "read",
    "read": "read",
    "find": "read",
    "search": "read",
    "list": "read",
    "browse": "read",
}
COMPLEXITY_NODES = (
    ast.If,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.Try,
    ast.With,
    ast.AsyncWith,
    ast.Match,
    ast.IfExp,
    ast.BoolOp,
    ast.ExceptHandler,
    ast.comprehension,
)
AST_PROGRESS_EVERY = max(1, int(os.getenv("LEGACY_ATLAS_AST_PROGRESS_EVERY", "100")))
logger = logging.getLogger(__name__)


@dataclass
class ParsedFunction:
    qname: str
    short_name: str
    file_path: str
    line_start: int
    line_end: int
    complexity: int
    calls: list[str] = field(default_factory=list)
    entities: set[str] = field(default_factory=set)
    entity_sequence: list[str] = field(default_factory=list)
    crud_ops: set[str] = field(default_factory=set)


@dataclass
class ParsedRepository:
    root_path: Path
    files_scanned: int
    functions: list[ParsedFunction]
    imports: list[tuple[str, str]]
    parse_errors: list[str]


class _FunctionAnalyzer(ast.NodeVisitor):
    def __init__(self) -> None:
        self.complexity = 1
        self.calls: list[str] = []
        self.entities: set[str] = set()
        self.entity_sequence: list[str] = []
        self.crud_ops: set[str] = set()

    def generic_visit(self, node: ast.AST) -> None:
        if isinstance(node, COMPLEXITY_NODES):
            self.complexity += 1
        super().generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        call_name = _resolve_callable_name(node.func)
        if call_name:
            self.calls.append(call_name)
            self._capture_tokens(call_name)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        self._capture_tokens(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        self._capture_tokens(node.attr)
        self.generic_visit(node)

    def _capture_tokens(self, raw: str) -> None:
        text = raw.lower().replace("_", ".")
        for token, entity in ENTITY_TOKENS.items():
            if token in text:
                self.entities.add(entity)
                self.entity_sequence.append(entity)
        for token, crud in CRUD_TOKENS.items():
            if token in text:
                self.crud_ops.add(crud)


class _RepositoryVisitor(ast.NodeVisitor):
    def __init__(self, module_name: str, file_path: str) -> None:
        self.module_name = module_name
        self.file_path = file_path
        self.class_stack: list[str] = []
        self.functions: list[ParsedFunction] = []
        self.imports: list[tuple[str, str]] = []

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.append((self.module_name, alias.name))

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        base = node.module or ""
        for alias in node.names:
            imported = f"{base}.{alias.name}".strip(".")
            self.imports.append((self.module_name, imported))

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.class_stack.append(node.name)
        for statement in node.body:
            self.visit(statement)
        self.class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._record_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._record_function(node)

    def _record_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        fq_parts = [self.module_name, *self.class_stack, node.name]
        qname = ".".join(part for part in fq_parts if part)

        analyzer = _FunctionAnalyzer()
        for statement in node.body:
            analyzer.visit(statement)

        # Include hints from function name itself.
        analyzer._capture_tokens(node.name)

        self.functions.append(
            ParsedFunction(
                qname=qname,
                short_name=node.name,
                file_path=self.file_path,
                line_start=node.lineno,
                line_end=getattr(node, "end_lineno", node.lineno),
                complexity=analyzer.complexity,
                calls=analyzer.calls,
                entities=analyzer.entities,
                entity_sequence=analyzer.entity_sequence,
                crud_ops=analyzer.crud_ops,
            )
        )


def _resolve_callable_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _resolve_callable_name(node.value)
        if parent:
            return f"{parent}.{node.attr}"
        return node.attr
    if isinstance(node, ast.Call):
        return _resolve_callable_name(node.func)
    return None


def _module_name_from_path(root: Path, file_path: Path) -> str:
    relative = file_path.relative_to(root)
    parts = list(relative.parts)
    if parts[-1].endswith(".py"):
        parts[-1] = parts[-1][:-3]
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def iter_python_files(root: Path, max_files: int = 1000) -> Iterable[Path]:
    count = 0
    for path in root.rglob("*.py"):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        if count >= max_files:
            break
        count += 1
        yield path


def analyze_python_repository(root: Path) -> ParsedRepository:
    logger.info("AST analyzer started root=%s", root)
    functions: list[ParsedFunction] = []
    imports: list[tuple[str, str]] = []
    parse_errors: list[str] = []
    files_scanned = 0

    for file_path in iter_python_files(root):
        files_scanned += 1
        if files_scanned % AST_PROGRESS_EVERY == 0:
            logger.info("AST analyzer progress root=%s files_scanned=%s", root, files_scanned)
        rel_file = str(file_path.relative_to(root))
        module_name = _module_name_from_path(root, file_path)
        try:
            source = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            source = file_path.read_text(encoding="latin-1")

        try:
            tree = ast.parse(source, filename=rel_file)
        except SyntaxError as exc:
            parse_errors.append(f"{rel_file}:{exc.lineno}:{exc.offset} {exc.msg}")
            logger.debug("AST parse syntax error file=%s line=%s msg=%s", rel_file, exc.lineno, exc.msg)
            continue

        visitor = _RepositoryVisitor(module_name=module_name, file_path=rel_file)
        visitor.visit(tree)
        functions.extend(visitor.functions)
        imports.extend(visitor.imports)

    logger.info(
        "AST analyzer completed root=%s files=%s functions=%s imports=%s parse_errors=%s",
        root,
        files_scanned,
        len(functions),
        len(imports),
        len(parse_errors),
    )

    return ParsedRepository(
        root_path=root,
        files_scanned=files_scanned,
        functions=functions,
        imports=imports,
        parse_errors=parse_errors,
    )


def build_call_graph(functions: list[ParsedFunction]) -> list[tuple[str, str]]:
    exact_lookup = {function.qname: function.qname for function in functions}
    short_lookup: dict[str, set[str]] = defaultdict(set)
    for function in functions:
        short_lookup[function.short_name].add(function.qname)

    edges: set[tuple[str, str]] = set()
    for function in functions:
        for call in function.calls:
            direct_match = exact_lookup.get(call)
            if direct_match:
                edges.add((function.qname, direct_match))
                continue

            short_name = call.split(".")[-1]
            candidates = short_lookup.get(short_name, set())
            if len(candidates) == 1:
                edges.add((function.qname, next(iter(candidates))))

    return sorted(edges)


def compute_degrees(edges: list[tuple[str, str]]) -> tuple[dict[str, int], dict[str, int]]:
    out_degree: Counter[str] = Counter()
    in_degree: Counter[str] = Counter()
    for source, target in edges:
        out_degree[source] += 1
        in_degree[target] += 1
    return dict(out_degree), dict(in_degree)


def count_entities(functions: list[ParsedFunction]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for function in functions:
        for entity in function.entities:
            counter[entity] += 1
    return counter
