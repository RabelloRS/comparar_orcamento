import logging
import os
from datetime import datetime
from pathlib import Path
import json

class SystemLogger:
    """Sistema de logs centralizado para todas as ferramentas"""
    
    def __init__(self, log_dir="logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Configuração básica do logging
        self.setup_loggers()
    
    def setup_loggers(self):
        """Configura os diferentes loggers do sistema"""
        
        # Logger principal do sistema
        self.system_logger = self._create_logger(
            'system', 
            self.log_dir / 'system.log',
            logging.INFO
        )
        
        # Logger para busca semântica
        self.search_logger = self._create_logger(
            'search', 
            self.log_dir / 'busca_semantica.log',
            logging.DEBUG
        )
        
        # Logger para análise de dados
        self.analysis_logger = self._create_logger(
            'analysis', 
            self.log_dir / 'analise_dados.log',
            logging.DEBUG
        )
        
        # Logger para configurações
        self.config_logger = self._create_logger(
            'config', 
            self.log_dir / 'configuracoes.log',
            logging.DEBUG
        )
        
        # Logger para backend
        self.backend_logger = self._create_logger(
            'backend', 
            self.log_dir / 'backend.log',
            logging.DEBUG
        )
        
        # Logger para API
        self.api_logger = self._create_logger(
            'api', 
            self.log_dir / 'api_requests.log',
            logging.DEBUG
        )
        
        # Logger para erros
        self.error_logger = self._create_logger(
            'errors', 
            self.log_dir / 'errors.log',
            logging.ERROR
        )
    
    def _create_logger(self, name, log_file, level):
        """Cria um logger específico"""
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # Remove handlers existentes para evitar duplicação
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Handler para arquivo
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        
        # Handler para console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # Formato das mensagens
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def log_search_request(self, query, top_k, user_ip=None):
        """Log de requisições de busca"""
        self.search_logger.info(f"Busca realizada: '{query}' | top_k: {top_k} | IP: {user_ip}")
    
    def log_search_results(self, query, results_count, execution_time):
        """Log de resultados de busca"""
        self.search_logger.info(f"Resultados: {results_count} itens para '{query}' | Tempo: {execution_time:.2f}s")
    
    def log_search_error(self, query, error_msg):
        """Log de erros na busca"""
        self.search_logger.error(f"Erro na busca '{query}': {error_msg}")
        self.error_logger.error(f"SEARCH_ERROR: {query} - {error_msg}")
    
    def log_data_analysis(self, operation, file_name=None, records_count=None):
        """Log de operações de análise de dados"""
        msg = f"Análise: {operation}"
        if file_name:
            msg += f" | Arquivo: {file_name}"
        if records_count:
            msg += f" | Registros: {records_count}"
        self.analysis_logger.info(msg)
    
    def log_config_change(self, setting, old_value, new_value, user_ip=None):
        """Log de mudanças de configuração"""
        self.config_logger.info(f"Configuração alterada: {setting} | {old_value} -> {new_value} | IP: {user_ip}")
    
    def log_backend_operation(self, operation, status, details=None):
        """Log de operações do backend"""
        msg = f"Backend {operation}: {status}"
        if details:
            msg += f" | {details}"
        self.backend_logger.info(msg)
    
    def log_api_request(self, endpoint, method, status_code, response_time, user_ip=None):
        """Log de requisições da API"""
        self.api_logger.info(f"{method} {endpoint} | Status: {status_code} | Tempo: {response_time:.3f}s | IP: {user_ip}")
    
    def log_system_event(self, event, details=None):
        """Log de eventos do sistema"""
        msg = f"Sistema: {event}"
        if details:
            msg += f" | {details}"
        self.system_logger.info(msg)
    
    def log_error(self, component, error_msg, exception=None):
        """Log de erros gerais"""
        msg = f"{component}: {error_msg}"
        if exception:
            msg += f" | Exception: {str(exception)}"
        self.error_logger.error(msg)
    
    def log_performance(self, operation, execution_time, memory_usage=None):
        """Log de performance"""
        msg = f"Performance {operation}: {execution_time:.3f}s"
        if memory_usage:
            msg += f" | Memória: {memory_usage}MB"
        self.system_logger.info(msg)
    
    def export_logs_summary(self, start_date=None, end_date=None):
        """Exporta resumo dos logs"""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'period': {
                'start': start_date.isoformat() if start_date else None,
                'end': end_date.isoformat() if end_date else None
            },
            'log_files': []
        }
        
        for log_file in self.log_dir.glob('*.log'):
            if log_file.exists():
                stat = log_file.stat()
                summary['log_files'].append({
                    'name': log_file.name,
                    'size_bytes': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        summary_file = self.log_dir / f'logs_summary_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        return summary_file

# Instância global do logger
logger = SystemLogger()

# Funções de conveniência
def log_search(query, top_k, user_ip=None):
    logger.log_search_request(query, top_k, user_ip)

def log_search_results(query, count, time):
    logger.log_search_results(query, count, time)

def log_search_error(query, error):
    logger.log_search_error(query, error)

def log_analysis(operation, file_name=None, records=None):
    logger.log_data_analysis(operation, file_name, records)

def log_config(setting, old_val, new_val, user_ip=None):
    logger.log_config_change(setting, old_val, new_val, user_ip)

def log_backend(operation, status, details=None):
    logger.log_backend_operation(operation, status, details)

def log_api(endpoint, method, status, time, user_ip=None):
    logger.log_api_request(endpoint, method, status, time, user_ip)

def log_system(event, details=None):
    logger.log_system_event(event, details)

def log_error(component, error, exception=None):
    logger.log_error(component, error, exception)

def log_performance(operation, time, memory=None):
    logger.log_performance(operation, time, memory)