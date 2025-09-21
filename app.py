from models.restaurante import Restaurante
from models.cardapio.bebida import Bebida
from models.cardapio.prato import Prato

restaurante_praca = Restaurante('praça', 'Gourmet')
bebida_suco = Bebida('Suco de melancia', 5.0, 'Grande')
prato_pao = Prato('Pao', 2.0, 'O melhor da cidade')
restaurante_praca.add_cardapio(bebida_suco)
restaurante_praca.add_cardapio(prato_pao)

def main():
    restaurante_praca.exibir_cardapio

if __name__ == '__main__':
    main()