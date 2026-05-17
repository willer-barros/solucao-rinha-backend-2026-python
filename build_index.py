import gzip
import json
import numpy as np
from usearch.index import Index

def build():
    print("Processamento iniciado")
    print("Lendo o arquivo references.json.gz")
    
    labels = []
    vectors = []
    
    try:
        with gzip.open("data/references.json.gz", "rt", encoding="utf-8") as f:
            # Estratégia 1: Tentar ler como JSON Lines (uma linha por registro)
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    # Se a linha começar com colchete ou vírgula (JSON tradicional mal quebrado)
                    if line.startswith('[') or line.startswith(','):
                        line = line.lstrip('[,')
                    if line.endswith(']') or line.endswith(','):
                        line = line.rstrip('],')
                    if not line:
                        continue
                        
                    data = json.loads(line)
                    # Ajuste aqui os nomes exatos das chaves do seu objeto, ex: data['id'] ou data['label']
                    # Supondo que a estrutura tenha 'id' (int) e 'vector' (lista de 14 floats)
                    labels.append(int(data['id']))
                    vectors.append(data['vector'])
                except Exception:
                    # Se falhar a linha, pode ser que o arquivo seja um JSON único completo
                    continue
            
            # Estratégia 2: Se não leu nada por linha, tenta decodificar o arquivo inteiro como um único array JSON
            if len(labels) == 0:
                f.seek(0)
                try:
                    full_data = json.loads(f.read())
                    if isinstance(full_data, list):
                        for data in full_data:
                            labels.append(int(data['id']))
                            vectors.append(data['vector'])
                except Exception as e:
                    print(f"Falha ao tentar ler como JSON único: {e}")

    except Exception as e:
        print(f"Erro crítico na abertura/leitura do arquivo físico: {e}")

    print(f"[BUILD] Total de {len(labels)} vetores lidos e indexados.")

    if len(labels) == 0:
        raise ValueError("ERRO CRÍTICO: Nenhum registro foi extraído do arquivo references.json.gz! Verifique se o arquivo possui dados ou se as chaves 'id' e 'vector' estão corretas.")

    # Inicializa o Index do USearch com a dimensão correta
    index = Index(ndim=14, metric='l2sq', dtype='f32')
    
    # Adiciona os vetores no indexador
    print("[BUILD] Populando o índice USearch...")
    vectors_array = np.array(vectors, dtype=np.float32)
    labels_array = np.array(labels, dtype=np.uint32) # Garante espaço para IDs grandes
    
    index.add(labels_array, vectors_array)

    # 3. Salvar os arquivos binários finais na pasta data
    print("[BUILD] Exportando arquivo de índice do USearch...")
    index.save("data/rinha_usearch.index")
    
    print("[BUILD] Exportando arquivo labels.bin...")
    # Salvamos como uint32 ou uint8 dependendo do tamanho do seu ID
    final_labels = np.array(labels, dtype=np.uint32)
    final_labels.tofile("data/labels.bin")
    
    print(f"[BUILD] Tamanho final do arquivo de labels: {final_labels.nbytes} bytes.")
    print("=== [BUILD] Processo concluído com sucesso! ===")

if __name__ == "__main__":
    build()