#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: Gustavo R. Anjos
# Email: gustavo.rabello@coppe.ufrj.br
# Date: 2026-05-31
# File: student_aliases.py

import re
import unicodedata

PARTICLES = {'da', 'das', 'de', 'do', 'dos', 'e'}


def _normalize(value):
    value = unicodedata.normalize('NFKD', value)
    value = ''.join(char for char in value if not unicodedata.combining(char))
    return ' '.join(re.sub(r'[^a-z0-9]+', ' ', value.lower()).split())


def _aliases_for_tokens(tokens):
    aliases = set()
    if not tokens:
        return aliases

    aliases.add(' '.join(tokens))
    max_family = min(3, len(tokens))
    for family_size in range(1, max_family + 1):
        family_tokens = tokens[-family_size:]
        given_tokens = tokens[:-family_size]
        family = ' '.join(family_tokens)
        aliases.add(family)
        if not given_tokens:
            continue

        given = ' '.join(given_tokens)
        first = given_tokens[0]
        initials = ' '.join(token[0] for token in given_tokens)
        aliases.update({
            '{} {}'.format(family, given),
            '{} {}'.format(given, family),
            '{} {}'.format(family, first),
            '{} {}'.format(first, family),
            '{} {}'.format(family, initials),
            '{} {}'.format(initials, family),
        })

    return aliases


def _aliases_for_name(name):
    normalized = _normalize(name)
    all_tokens = normalized.split()
    significant_tokens = [
        token for token in all_tokens
        if token not in PARTICLES
    ]

    aliases = {normalized}
    aliases.update(_aliases_for_tokens(all_tokens))
    aliases.update(_aliases_for_tokens(significant_tokens))
    return {alias.strip() for alias in aliases if alias.strip()}


STUDENT_AUTHOR_NAMES = {
    'afranioAugustoGomesGoncalves': [
        'Afrânio Augusto Gomes Gonçalves',
    ],
    'alexFragaRocha': [
        'Alex Fraga Rocha',
    ],
    'alineBarbosaFigueiredo': [
        'Aline Barbosa Figueiredo',
    ],
    'anaMariaDantasBalmant': [
        'Ana Maria Dantas Balmant',
    ],
    'annaCoimbra': [
        'Anna Barbara Serejo Coimbra',
        'Anna Bárbara Serejo Coimbra',
    ],
    'antonioEmanuel': [
        'Antonio Emanuel Marques dos Santos',
    ],
    'antonioViniciusVarandasPires': [
        'Antonio Vinícius Varandas Pires',
    ],
    'brenoSarmento': [
        'Breno Mota Sarmento',
    ],
    'camilaBorgesSantos': [
        'Camila Borges Santos',
    ],
    'carinaSondermann': [
        'Carina Nogueira Sondermann',
    ],
    'carlosEchenique': [
        'Carlos Arturo Echenique Hernandez',
    ],
    'claraCostaHildebrandt': [
        'Clara Costa Hildebrandt',
    ],
    'dalvanOliveiraMendes': [
        'Dalvan Oliveira Mendes',
    ],
    'danielBarbedo': [
        'Daniel Barbedo Vasconcelos Santos',
    ],
    'danielMoreiraSpesani': [
        'Daniel Moreira Spesani',
    ],
    'daviCarvalhoLopesSouza': [
        'Davi Carvalho Lopes de Souza',
    ],
    'eduardoAquinoMenezesSoares': [
        'Eduardo Aquino Menezes Soares',
    ],
    'eduardoCorrea': [
        'Eduardo Dias Correa',
    ],
    'eduardoVitralFreigedoRodrigues': [
        'Eduardo Vitral Freigedo Rodrigues',
    ],
    'erikGros': [
        'Erik Gros',
    ],
    'fabioGasparJr': [
        'Fábio Gaspar Júnior',
        'Fabio Gaspar Santos Junior',
    ],
    'felipeFeres': [
        'Felipe Feres Ferreira',
        'Felipe Féres Ferreira',
    ],
    'felipeRodrigoMelloAlves': [
        'Felipe Rodrigo de Mello Alves',
    ],
    'gabrielAffonsoCostaWaehneldt': [
        'Gabriel Affonso Costa Waehneldt',
    ],
    'gabrielBraz': [
        'Gabriel Braz',
    ],
    'gabrielFelipeOliveiraAntao': [
        'Gabriel Felipe Oliveira Antão',
    ],
    'gabrielGarden': [
        'Gabriel de Lucas Garden',
    ],
    'gabrielSantosOliveira': [
        'Gabriel dos Santos Oliveira',
    ],
    'gabrielSilvaOliveiraNunesAguiar': [
        'Gabriel da Silva Oliveira Nunes de Aguiar',
    ],
    'gabrielSousa': [
        'Gabriel Ricardo Güntensperger Sousa',
    ],
    'gustavoBodstein': [
        'Prof. Gustavo Cesar Rachid Bodstein',
    ],
    'gustavoPradoFerreira': [
        'Gustavo Prado Ferreira',
    ],
    'heitorGomesSouzaBatista': [
        'Heitor Gomes de Souza Batista',
    ],
    'higorOdilon': [
        'Higor Odilon Gottgtroy',
    ],
    'igorMaielloMaia': [
        'Igor Maiello Maia',
    ],
    'jessicaAparecidaSilva': [
        'Jéssica Aparecida Silva',
    ],
    'joaoDeodatoBatistaSantos': [
        'João Deodato Batista dos Santos',
    ],
    'joaoInnocente': [
        'João Paulo Innocente de Souza',
    ],
    'joaoPedroRodrigues': [
        'João Pedro Rodrigues',
        'João Pedro Rodrigues Ferreira',
    ],
    'joaoSalgueiroLage': [
        'João Salgueiro Lage',
    ],
    'joaoVictorSantos': [
        'João Victor Barros dos Santos',
    ],
    'jorgeAngelAguileraLiendo': [
        'Jorge Angel Aguilera Liendo',
    ],
    'joseLagesSilvaNeto': [
        'Jose Lages da Silva Neto',
    ],
    'joseRicardoSilvaCerqueiraJunior': [
        'José Ricardo da Silva Cerqueira Junior',
    ],
    'joseViniciusVictorinoGomes': [
        'José Vinícius Victorino Gomes',
    ],
    'juanOliveiraSantos': [
        'Juan de Oliveira dos Santos',
    ],
    'julianaCalazans': [
        'Juliana Calazans de Cerqueira',
    ],
    'leandroMarquesSantos': [
        'Leandro Marques dos Santos',
    ],
    'leonardoAndSantosLeiteLuizAlbertoLoboNobrega': [
        'Leonardo and Santos Leite, Luiz Alberto Lobo da Nóbrega',
    ],
    'leonardoCostaLimaXavierMendonca': [
        'Leonardo da Costa Lima Xavier de Mendonça',
    ],
    'leonardoFernandoFerreira': [
        'Leonardo Fernando Ferreira',
    ],
    'leonardoVieiraCunha': [
        'Leonardo Vieira Cunha',
    ],
    'leonardoVotarelliReginiAndrade': [
        'Leonardo Votarelli Regini de Andrade',
    ],
    'lionel': [
        'Eng. Carlos Humberto Lionel',
    ],
    'lucasBorgesMenezes': [
        'Lucas Borges Menezes',
    ],
    'lucasCarvalhoSousa': [
        'Lucas Carvalho de Sousa',
    ],
    'lucasMiranda': [
        'Lucas Mendes Miranda',
    ],
    'luisHenriqueCarnevaleCunha': [
        'Luis Henrique Carnevale da Cunha',
    ],
    'mateusDuarteOliveira': [
        'Mateus Duarte de Oliveira',
    ],
    'mateusMesquitaTeixeira': [
        'Mateus Mesquita Teixeira',
    ],
    'matheusCunhaRamalho': [
        'Matheus da Cunha Ramalho',
    ],
    'matheusDiasRocha': [
        'Matheus Dias da Rocha',
    ],
    'matheusFerreiraGomes': [
        'Matheus Ferreira Gomes',
    ],
    'pauloRobertoBertiLeiteFilho': [
        'Paulo Roberto Berti Leite Filho',
    ],
    'pedroHenriqueParanhosLima': [
        'Pedro Henrique Paranhos Lima',
    ],
    'pedroKropfAzevedo': [
        'Pedro Kropf de Azevedo',
    ],
    'pedroMattosSilva': [
        'Pedro Mattos da Silva',
    ],
    'pedroMorelRosa': [
        'Pedro Morel Rosa',
    ],
    'quentinDevorsine': [
        'Quentin Devorsine',
    ],
    'rafaelAlvesSilvaFilomeno': [
        'Rafael Alves da Silva Filomeno',
    ],
    'rafaelVidal': [
        'Rafael Araújo Vidal',
    ],
    'ramonChristianMoreiraGomesMendesJuvenal': [
        'Ramon Christian Moreira Gomes Mendes Juvenal',
    ],
    'raphaelViggianoFreitas': [
        'Raphael Viggiano Neves de Freitas',
    ],
    'renatoRosaOliveira': [
        'Renato Rosa Oliveira',
    ],
    'roberta': [
        'Jaciara Roberta Oliveira de Souza',
    ],
    'rodolfoRafaelPalaciosCarrasco': [
        'Rodolfo Rafael Palacios Carrasco',
    ],
    'rodrigoCamaraPatricio': [
        'Rodrigo Augusto Camara Patricio',
    ],
    'rodrigoDutra': [
        'Rodrigo Gadelha Salvaterra Dutra',
    ],
    'rodrigoFreixaAlbuquerqueEMello': [
        'Rodrigo Freixa de Albuquerque e Mello',
    ],
    'rodrigoSeefelderAssisAraujo': [
        'Rodrigo Seefelder de Assis Araújo',
    ],
    'thyagoAraujoCapitanio': [
        'Thyago Araújo Capitanio',
    ],
    'tiagoAlvesCalvanoAmaral': [
        'Tiago Alves Calvano do Amaral',
    ],
    'victorGuidoPinheiro': [
        'Victor Guido Pinheiro',
    ],
    'victorRiegerQueirozGoncalves': [
        'Victor Rieger Queiroz Gonçalves',
    ],
    'viniciusWaldilemeCoelhoMota': [
        'Vinicius Waldileme Coelho Mota',
    ],
    'vitorTavaresFontenele': [
        'Vitor Tavares Fontenele',
    ],
    'yanYanomamiFonteEloy': [
        'Yan Yanomami da Fonte Eloy',
    ],
    'ygorSilvaFlorentino': [
        'Ygor da Silva Florentino',
    ],
    'yuriPaesGomes': [
        'Yuri Paes Gomes',
    ],
}

STUDENT_EXTRA_ALIASES = {
    'fabioGasparJr': {
        'gaspar santos fabio',
        'gaspar santos f',
        'gaspar f g s',
        'f g s gaspar',
        'junior f g s',
        'f g s junior',
    },
    'joseLagesSilvaNeto': {
        'lages jose',
        'jose lages',
        'lages j',
        'j lages',
    },
}

STUDENT_AUTHOR_ALIASES = {}
for slug, names in STUDENT_AUTHOR_NAMES.items():
    aliases = set()
    for name in names:
        aliases.update(_aliases_for_name(name))
    aliases.update(STUDENT_EXTRA_ALIASES.get(slug, set()))
    STUDENT_AUTHOR_ALIASES[slug] = aliases
