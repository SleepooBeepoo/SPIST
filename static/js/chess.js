// Chess Game Implementation with Three Difficulty Levels

document.addEventListener('DOMContentLoaded', () => {
    console.log('Chess game initializing...');
    
    // Check if required libraries are loaded
    if (typeof Chess !== 'function') {
        console.error('Chess.js library not loaded properly!');
        document.getElementById('game-status').textContent = 'Error: Chess library not loaded';
        return;
    }
    
    if (typeof $ === 'undefined') {
        console.error('jQuery not loaded!');
        document.getElementById('game-status').textContent = 'Error: jQuery not loaded';
        return;
    }
    
    if (typeof Chessboard === 'undefined') {
        console.error('Chessboard.js not loaded!');
        document.getElementById('game-status').textContent = 'Error: Chessboard library not loaded';
        return;
    }
    
    // Initialize variables
    let board = null;
    let game = new Chess();
    let difficulty = 'easy'; // Default difficulty
    let playerColor = 'w'; // Player is white by default
    let computerThinking = false;
    
    // DOM elements
    const gameStatus = document.getElementById('game-status');
    const easyButton = document.getElementById('easy-button');
    const mediumButton = document.getElementById('medium-button');
    const hardButton = document.getElementById('hard-button');
    const resetButton = document.getElementById('reset-button');
    
    // Check if DOM elements exist
    if (!gameStatus || !easyButton || !mediumButton || !hardButton || !resetButton) {
        console.error('Required DOM elements not found!');
        return;
    }
    
    // Configuration for the chessboard
    const config = {
        draggable: true,
        position: 'start',
        onDragStart: onDragStart,
        onDrop: onDrop,
        onSnapEnd: onSnapEnd,
        pieceTheme: 'https://chessboardjs.com/img/chesspieces/wikipedia/{piece}.png'
    };
    
    // Initialize the board
    try {
        // Check if the chess-board element exists
        const boardElement = document.getElementById('chess-board');
        if (!boardElement) {
            console.error('Chess board element not found!');
            gameStatus.textContent = 'Error: Chess board element not found';
            return;
        }
        
        board = Chessboard('chess-board', config);
        console.log('Chessboard initialized successfully');
    } catch (error) {
        console.error('Error initializing chessboard:', error);
        gameStatus.textContent = 'Error initializing chessboard';
        return;
    }
    
    // Event listeners for difficulty buttons
    easyButton.addEventListener('click', () => {
        startNewGame('easy');
    });
    
    mediumButton.addEventListener('click', () => {
        startNewGame('medium');
    });
    
    hardButton.addEventListener('click', () => {
        startNewGame('hard');
    });
    
    resetButton.addEventListener('click', () => {
        resetGame();
    });
    
    // Function to start a new game with selected difficulty
    function startNewGame(selectedDifficulty) {
        game = new Chess();
        board.position('start');
        difficulty = selectedDifficulty;
        playerColor = 'w'; // Player always starts as white
        gameStatus.textContent = `Game started - ${capitalizeFirstLetter(difficulty)} difficulty`;
    }
    
    // Function to reset the game
    function resetGame() {
        game = new Chess();
        board.position('start');
        gameStatus.textContent = 'Select difficulty to start';
    }
    
    // Function to handle the start of a drag
    function onDragStart(source, piece) {
        // Do not pick up pieces if the game is over or it's not the player's turn
        if (game.game_over() || computerThinking || 
            (game.turn() === 'w' && piece.search(/^b/) !== -1) ||
            (game.turn() === 'b' && piece.search(/^w/) !== -1) ||
            (game.turn() !== playerColor[0])) {
            return false;
        }
    }
    
    // Function to handle when a piece is dropped
    function onDrop(source, target) {
        // Check if the move is legal
        const move = game.move({
            from: source,
            to: target,
            promotion: 'q' // Always promote to a queen for simplicity
        });
        
        // If illegal move, return piece to source square
        if (move === null) return 'snapback';
        
        // Update status
        updateStatus();
        
        // Make computer move after a short delay
        setTimeout(makeComputerMove, 250);
    }
    
    // Function to update the board position after the piece snap animation
    function onSnapEnd() {
        board.position(game.fen());
    }
    
    // Function to make a computer move based on difficulty
    function makeComputerMove() {
        if (game.game_over()) return;
        
        computerThinking = true;
        gameStatus.textContent = 'Computer is thinking...';
        
        // Use setTimeout to give UI time to update
        setTimeout(() => {
            const move = getBestMove(difficulty);
            game.move(move);
            board.position(game.fen());
            updateStatus();
            computerThinking = false;
        }, 500);
    }
    
    // Function to get the best move based on difficulty
    function getBestMove(difficulty) {
        const possibleMoves = game.moves();
        
        // If no moves available, return
        if (possibleMoves.length === 0) return null;
        
        // For easy difficulty: make random moves with occasional mistakes
        if (difficulty === 'easy') {
            return possibleMoves[Math.floor(Math.random() * possibleMoves.length)];
        }
        
        // For medium and hard difficulties: evaluate moves and choose based on score
        let bestMove = null;
        let bestValue = -9999;
        
        // Depth of search based on difficulty
        const depth = difficulty === 'medium' ? 2 : 3;
        
        // Evaluate each move
        for (let i = 0; i < possibleMoves.length; i++) {
            const move = possibleMoves[i];
            game.move(move);
            
            // Medium: sometimes make suboptimal moves
            if (difficulty === 'medium' && Math.random() < 0.3) {
                game.undo();
                return possibleMoves[Math.floor(Math.random() * possibleMoves.length)];
            }
            
            const value = -minimax(depth - 1, -10000, 10000, false);
            game.undo();
            
            if (value > bestValue) {
                bestValue = value;
                bestMove = move;
            }
        }
        
        return bestMove;
    }
    
    // Minimax algorithm with alpha-beta pruning for move evaluation
    function minimax(depth, alpha, beta, isMaximizingPlayer) {
        if (depth === 0) {
            return evaluateBoard();
        }
        
        const possibleMoves = game.moves();
        
        if (isMaximizingPlayer) {
            let bestValue = -9999;
            for (let i = 0; i < possibleMoves.length; i++) {
                game.move(possibleMoves[i]);
                bestValue = Math.max(bestValue, minimax(depth - 1, alpha, beta, !isMaximizingPlayer));
                game.undo();
                alpha = Math.max(alpha, bestValue);
                if (beta <= alpha) {
                    return bestValue;
                }
            }
            return bestValue;
        } else {
            let bestValue = 9999;
            for (let i = 0; i < possibleMoves.length; i++) {
                game.move(possibleMoves[i]);
                bestValue = Math.min(bestValue, minimax(depth - 1, alpha, beta, !isMaximizingPlayer));
                game.undo();
                beta = Math.min(beta, bestValue);
                if (beta <= alpha) {
                    return bestValue;
                }
            }
            return bestValue;
        }
    }
    
    // Function to evaluate the board position
    function evaluateBoard() {
        let totalEvaluation = 0;
        for (let i = 0; i < 8; i++) {
            for (let j = 0; j < 8; j++) {
                totalEvaluation += getPieceValue(game.board()[i][j], i, j);
            }
        }
        return totalEvaluation;
    }
    
    // Function to get the value of a piece
    function getPieceValue(piece, x, y) {
        if (piece === null) {
            return 0;
        }
        
        // Piece values
        const pieceValues = {
            'p': 10,  // pawn
            'n': 30,  // knight
            'b': 30,  // bishop
            'r': 50,  // rook
            'q': 90,  // queen
            'k': 900  // king
        };
        
        // Position bonuses (simplified)
        const positionBonus = 0.1 * (4 - Math.abs(3.5 - x) - Math.abs(3.5 - y));
        
        const absoluteValue = pieceValues[piece.type] + positionBonus;
        return piece.color === 'w' ? absoluteValue : -absoluteValue;
    }
    
    // Function to update the game status
    function updateStatus() {
        let status = '';
        
        if (game.in_checkmate()) {
            status = game.turn() === 'w' ? 'Computer wins! White is in checkmate.' : 'Congratulations, You Won! Black is in checkmate.';
        } else if (game.in_draw()) {
            status = 'Game over - Draw';
        } else if (game.in_check()) {
            status = game.turn() === 'w' ? 'White is in check' : 'Black is in check';
        } else {
            status = game.turn() === 'w' ? 'Your turn (White)' : 'Computer thinking...';
        }
        
        gameStatus.textContent = status;
    }
    
    // Helper function to capitalize first letter
    function capitalizeFirstLetter(string) {
        return string.charAt(0).toUpperCase() + string.slice(1);
    }
});