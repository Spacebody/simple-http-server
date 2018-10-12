#include <stdio.h>
#include <string.h>
#include <unistd.h>

#define START_CMD 0
#define STOP_CMD 1
#define RESTART_CMD 2
#define STATUS_CMD 3
#define EXIT_CMD 4
#define LIST_CMD 5

int search(char *commands[], char *str, int length){
    int i = 0;
    while(i < length){
        if(strcmp(commands[i], str) == 0){
            return i;
        }
        i++;
    }
    return -1;
}

void print_list(char *commands[], int length) {
    for (int i = 0; i < length; ++i) {
        if (commands[i] != NULL){
            printf("%s\n", commands[i]);
        }
    }
}

int main(){
    char *commands[6] = {"start","stop","restart","status","exit","list"};
    int length = sizeof(commands)/ sizeof(commands[0]);
    printf("%d\n",length);
    int switch_var = 0;//The variable which presents the status of the program
    char input[1024];//Get the input
    char charTemp;
    int a;//The number of the command list

    printf("Please enter a command, or enter 'list' to see all the command you can use:");
    scanf("%s", input);
    a = search(commands, input, length);

    while (a == -1){
        printf("You have entered an unrecognized command, so we automatically list all the commands that you can use------\n");
        print_list(commands, length);
        while((charTemp = getchar()) != '\n' && charTemp != EOF);
        printf("Now, please enter a command:");
        scanf("%s\n", input);
        while((charTemp = getchar()) != '\n' && charTemp != EOF);
        a = search(commands, input, length);
        printf("%d",a);
    }

    while(switch_var != 3){
        switch (a){
            case START_CMD:
                if (switch_var == 0){
                    printf("You have started this program!\n");
                    switch_var = 1;
                } else{
                    printf("The program is already on!\n");
                }
                break;
            case STOP_CMD:
                if (switch_var == 1){
                    printf("You have stopped this program!\n");
                    switch_var = 0;
                } else{
                    printf("The program is already closed!\n");
                }
                break;
            case RESTART_CMD:
                if (switch_var ==1 ){
                    printf("Stopping the program now...\n");
                    sleep(2);
                    printf("Restarting the program now...\n");
                    sleep(2);
                    printf("You have restarted the program!\n");
                    switch_var = 1;
                } else{
                    printf("The program is closed now! Please start it before restart it!\n");
                }
                break;
            case STATUS_CMD:
                if (switch_var == 1){
                    printf("The program is running now.\n");
                }else {
                    printf("The program is not running.\n");
                }
                break;
            case EXIT_CMD:
                switch_var = 3;
                printf("You have exited the program now. See you next time!");
                break;
            case LIST_CMD:
                printf("You can execute the following commands:\n");
                print_list(commands, length);
                break;
            default:
                printf("You have entered an unrecognized command, so we automatically list all the commands that you can use------\n");
                print_list(commands, length);
                break;
        }
        if (switch_var != 3){
            printf("What do you want to do next?  Please enter a command: ");
            scanf("%s", input);
            a = search(commands, input, length);
            if (a == -1){
                printf("You have entered an unrecognized command, so we automatically list all the commands that you can use------\n");
                print_list(commands, length);
            }
        }
    }
}