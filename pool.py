import requests
import os
import subprocess
import time
from config import (
    API_URL,
    POOL_TOKEN,
    ADDITIONAL_ADDRESS,
    BATCH_SIZE,
    SLEEP_TIME
)
from typing import List, Dict, Optional
import logging
import re
from tenacity import retry, stop_after_attempt, wait_exponential
from enum import Enum

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Mover para config.py
GPU_SETTINGS = {
    "threads": "0",
    "gpu_id": "0",
    "grid_size": "1536"
}

class ProgramState(Enum):
    INITIALIZING = "initializing"
    FETCHING = "fetching"
    PROCESSING = "processing"
    ERROR = "error"
    COMPLETED = "completed"

def clear_screen():
    """Limpa a tela do terminal."""
    os.system('cls' if os.name == 'nt' else 'clear')

def fetch_block_data() -> Optional[Dict]:
    headers = {"pool-token": POOL_TOKEN}
    try:
        response = requests.get(API_URL, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.Timeout:
        logging.error("Timeout ao buscar dados do bloco")
    except requests.RequestException as e:
        logging.error(f"Erro ao fazer a requisição: {e}")
    return None

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def fetch_block_data_with_retry() -> Optional[Dict]:
    """
    Busca dados do bloco com retry automático em caso de falha.
    """
    return fetch_block_data()

def validate_address(address: str) -> bool:
    """
    Valida se o endereço Bitcoin é válido.
    
    Args:
        address: Endereço Bitcoin a ser validado
        
    Returns:
        bool: True se o endereço é válido, False caso contrário
    """
    # Padrão básico para endereços Bitcoin
    pattern = r'^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$'
    return bool(re.match(pattern, address))

def save_addresses_to_file(
    addresses: List[str], 
    additional_address: str, 
    filename: str = "in.txt"
) -> None:
    if not addresses:
        logging.error("Lista de endereços vazia")
        return
        
    if not validate_address(additional_address):
        logging.error(f"Endereço adicional inválido: {additional_address}")
        return
        
    try:
        with open(filename, "w") as file:
            for address in addresses:
                file.write(address + "\n")
            file.write(additional_address + "\n")  # Adicionando o endereço adicional
        logging.info("Endereços salvos com sucesso")
    except Exception as e:
        logging.error(f"Erro ao salvar endereços no arquivo: {e}")

def clear_file(filename):
    try:
        with open(filename, "w") as file:
            pass
        print(f"Arquivo '{filename}' limpo com sucesso.")
    except Exception as e:
        print(f"Erro ao limpar o arquivo '{filename}': {e}")

def run_program(start: str, end: str) -> None:
    command = [
        "./vanitysearch",
        "-t", GPU_SETTINGS["threads"],
        "-gpu",
        "-gpuId", GPU_SETTINGS["gpu_id"],
        "-g", GPU_SETTINGS["grid_size"],
        "-i", "in.txt",
        "-o", "out.txt",
        "--keyspace", f"{start}:{end}"
    ]
    try:
        logging.info(f"Executando o programa com keyspace {f'{start}:{end}'}...")
        subprocess.run(command, check=True)
        logging.info("Programa executado com sucesso.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Erro ao executar o programa: {e}")
    except Exception as e:
        logging.error(f"Erro inesperado: {e}")

def post_private_keys(private_keys: List[str]) -> bool:
    """
    Envia chaves privadas para a API.
    
    Args:
        private_keys: Lista de chaves privadas
        
    Returns:
        bool: True se o envio foi bem sucedido, False caso contrário
    """
    headers = {
        "pool-token": POOL_TOKEN,
        "Content-Type": "application/json"
    }
    data = {"privateKeys": private_keys}
    
    logging.info(f"Enviando {len(private_keys)} chaves privadas")
    
    try:
        with requests.Session() as session:
            response = session.post(API_URL, headers=headers, json=data)
            response.raise_for_status()
            logging.info("Chaves privadas enviadas com sucesso")
            return True
    except requests.RequestException as e:
        logging.error(f"Erro ao fazer a requisição POST: {e}")
        return False

def process_out_file(
    out_file: str = "out.txt",
    in_file: str = "in.txt",
    additional_address: str = ADDITIONAL_ADDRESS
) -> bool:
    if not all(os.path.exists(f) for f in [out_file, in_file]):
        logging.error("Arquivos necessários não encontrados")
        return False

    private_keys = {}
    addresses = []
    found_additional_address = False

    try:
        # Lendo os endereços do arquivo in.txt
        with open(in_file, "r") as file:
            addresses = [line.strip() for line in file if line.strip()]
        
        # Removendo o endereço adicional para evitar inconsistência
        if additional_address in addresses:
            addresses.remove(additional_address)

        # Lendo os endereços e chaves privadas do arquivo out.txt
        with open(out_file, "r") as file:
            current_address = None
            for line in file:
                if "Pub Addr: " in line:
                    current_address = line.split("Pub Addr: ")[1].strip()
                elif "Priv (HEX): " in line and current_address:
                    private_key = line.split("Priv (HEX): ")[1].strip()
                    private_keys[current_address] = private_key
                    # Verificando se é a chave do endereço adicional
                    if current_address == additional_address:
                        found_additional_address = True

        # Se a chave privada do endereço adicional foi encontrada
        if found_additional_address:
            print("Chave privada do endereço adicional encontrada! Parando o programa.")
            print(f"Chave encontrada: {private_keys.get(additional_address)}")
            return True

        # Verificando se a quantidade de chaves privadas corresponde à quantidade de endereços
        if len(private_keys) != len(addresses):
            print(f"Erro: Número de chaves privadas ({len(private_keys)}) não corresponde ao número de endereços ({len(addresses)}).")
            clear_file(out_file)
            return False

        # Ordenando as chaves privadas na mesma ordem dos endereços em in.txt
        ordered_private_keys = [private_keys[addr] for addr in addresses if addr in private_keys]

        # Enviar as chaves em lotes de 10
        for i in range(0, len(ordered_private_keys), 10):
            batch = ordered_private_keys[i:i + 10]
            if len(batch) == 10:
                post_private_keys(batch)
            else:
                print(f"Lote com menos de 10 chaves ignorado: {batch}")

    except (IOError, ValueError) as e:
        print(f"Erro ao processar os arquivos: {e}")

    # Limpar o arquivo out.txt
    clear_file(out_file)
    return False

def validate_block_data(block_data: Dict) -> bool:
    """
    Valida os dados do bloco recebidos da API.
    
    Args:
        block_data: Dicionário com os dados do bloco
        
    Returns:
        bool: True se os dados são válidos, False caso contrário
    """
    required_fields = ["checkwork_addresses", "range"]
    return all(field in block_data for field in required_fields)

def process_private_keys_batch(private_keys: List[str], batch_size: int = 10) -> None:
    """
    Processa as chaves privadas em lotes.
    
    Args:
        private_keys: Lista de chaves privadas
        batch_size: Tamanho do lote para processamento
    """
    total_keys = len(private_keys)
    for i in range(0, total_keys, batch_size):
        batch = private_keys[i:i + batch_size]
        if len(batch) == batch_size:
            if not post_private_keys(batch):
                logging.warning(f"Falha ao processar lote {i//batch_size + 1}")
        else:
            logging.info(f"Ignorando lote incompleto com {len(batch)} chaves")

def main() -> None:
    """Função principal do programa com controle de estado."""
    state = ProgramState.INITIALIZING
    retry_count = 0
    max_retries = 3
    
    while state != ProgramState.COMPLETED:
        try:
            if state == ProgramState.INITIALIZING:
                clear_screen()
                state = ProgramState.FETCHING
                
            elif state == ProgramState.FETCHING:
                block_data = fetch_block_data_with_retry()
                if block_data:
                    state = ProgramState.PROCESSING
                else:
                    raise ValueError("Falha ao buscar dados do bloco")
                    
            elif state == ProgramState.PROCESSING:
                if process_block():
                    state = ProgramState.COMPLETED
                    
        except KeyboardInterrupt:
            logging.info("Programa interrompido pelo usuário")
            break
        except Exception as e:
            logging.error(f"Erro no estado {state}: {e}")
            retry_count += 1
            if retry_count >= max_retries:
                state = ProgramState.ERROR
                break
            state = ProgramState.INITIALIZING
            time.sleep(SLEEP_TIME)

if __name__ == "__main__":
    main()
