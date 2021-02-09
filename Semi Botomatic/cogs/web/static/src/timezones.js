'use strict';

import FuzzySearch from 'fuzzy-search';


(function () {

    var input = document.getElementById('timezoneSearch')
    input.addEventListener('keydown', function (event) {

        const list = document.getElementById('timezoneList')
        const cards = list.getElementsByClassName('col-6')

        const searcher = new FuzzySearch(cards, ['innerText'], {caseSensitive: false})
        const search = searcher.search(document.getElementById('timezoneSearch').value)

        const results = Array.from(search)

        for (let index = 0; index < cards.length; index++) {
            if (results.includes(cards[index])) {
                cards[index].style.display = "";
            } else {
                cards[index].style.display = "none";
            }
        }

    })
})()
